import hashlib
import json
import uuid

from psycopg2.extras import Json

from common import calculate_snapshot_diff, deep_merge
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import AbstractDatasetRepository
from domain.datasets.value_objects import DatasetVersionParams
from infrastructure.database.postgres import PostgresClient


def _pop_fields(source: dict, field_names: list[str]) -> dict:
    """Extract and remove specified fields from source dict."""
    extracted = {}
    for key in field_names:
        if key in source:
            extracted[key] = source.pop(key)
    return extracted


def _strip_ods_volatile_fields(stripped: dict, volatile: dict) -> None:
    """Strip ODS-specific volatile fields (root + metas.default)."""
    # Root ODS fields
    ods_root = _pop_fields(
        stripped,
        [
            "updated_at",
            "data_processed",
            "metadata_processed",
            "api_call_count",
            "download_count",
            "popularity_score",
            "attachment_download_count",
            "file_field_download_count",
            "records_size",
        ],
    )
    volatile.update(ods_root)

    # ODS metas.default
    if "metas" in stripped and "default" in stripped["metas"]:
        default = stripped["metas"]["default"].copy()
        metas_volatile = _pop_fields(default, ["data_processed", "metadata_processed"])

        if metas_volatile:
            volatile.setdefault("metas", {})["default"] = metas_volatile

        stripped["metas"] = stripped["metas"].copy()
        stripped["metas"]["default"] = default


def _strip_datagouv_volatile_fields(stripped: dict, volatile: dict) -> None:
    """Strip DataGouv-specific volatile fields (metrics)."""
    if "metrics" not in stripped or not isinstance(stripped["metrics"], dict):
        return

    metrics = stripped["metrics"].copy()
    metrics_volatile = _pop_fields(
        metrics,
        [
            "views",
            "reuses",
            "followers",
            "datasets",
            "resources_downloads",
            "reuses_by_months",
            "followers_by_months",
        ],
    )

    if metrics_volatile:
        volatile["metrics"] = metrics_volatile
    stripped["metrics"] = metrics


def _strip_common_volatile_fields(stripped: dict, volatile: dict) -> None:
    """Strip common volatile fields (timestamps, quality, internal)."""
    # Global fields
    global_volatile = _pop_fields(
        stripped, ["last_modified", "last_update", "expected_update", "quality", "harvest", "resources"]
    )

    volatile.update(global_volatile)

    # Internal flags
    if "internal" in stripped:
        internal = stripped["internal"].copy()
        internal_volatile = _pop_fields(
            internal,
            ["last_modified_internal", "metadata_source_language", "catalog_site_contact", "last_update_internal"],
        )

        if internal_volatile:
            volatile.setdefault("internal", {}).update(internal_volatile)
        stripped["internal"] = internal


def strip_volatile_fields(data: dict) -> tuple[dict, dict]:
    """
    Removes fields that change frequently and returns them separately.
    Returns (stripped_data, volatile_data).
    """
    if not data:
        return data, {}

    stripped = data.copy()
    volatile = {}

    _strip_ods_volatile_fields(stripped, volatile)
    _strip_datagouv_volatile_fields(stripped, volatile)
    _strip_common_volatile_fields(stripped, volatile)

    return stripped, volatile


class PostgresDatasetRepository(AbstractDatasetRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def add(self, dataset: Dataset) -> None:
        self.client.execute(
            """
            INSERT INTO datasets (
                id, platform_id, buid, slug, title, page, publisher, created, modified, published, restricted, deleted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                platform_id = EXCLUDED.platform_id,
                buid = EXCLUDED.buid,
                slug = EXCLUDED.slug,
                title = EXCLUDED.title,
                page = EXCLUDED.page,
                publisher = EXCLUDED.publisher,
                created = EXCLUDED.created,
                modified = EXCLUDED.modified,
                published = EXCLUDED.published,
                restricted = EXCLUDED.restricted,
                deleted = EXCLUDED.deleted
            """,
            (
                str(dataset.id),
                str(dataset.platform_id),
                dataset.buid,
                str(dataset.slug),
                dataset.title,
                str(dataset.page),
                dataset.publisher,
                dataset.created,
                dataset.modified,
                dataset.published,
                dataset.restricted,
                dataset.is_deleted,
            ),
        )
        self.client.execute(
            "INSERT INTO dataset_quality (dataset_id, downloads_count, api_calls_count, has_description, is_slug_valid, evaluation_results) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
            "ON CONFLICT (dataset_id) DO UPDATE SET "
            "downloads_count = EXCLUDED.downloads_count, "
            "api_calls_count = EXCLUDED.api_calls_count, "
            "has_description = EXCLUDED.has_description, "
            "evaluation_results = EXCLUDED.evaluation_results, "
            "is_slug_valid = EXCLUDED.is_slug_valid",
            (
                str(dataset.id),
                dataset.quality.downloads_count,
                dataset.quality.api_calls_count,
                dataset.quality.has_description,
                dataset.quality.is_slug_valid,
                Json(dataset.quality.evaluation_results) if dataset.quality.evaluation_results else None,
            ),
        )

    def add_version(self, params: "DatasetVersionParams") -> None:
        """Add a new version of a dataset using Parameter Object pattern."""
        stripped, volatile = strip_volatile_fields(params.snapshot)

        diff = params.diff  # Start with provided diff

        if not diff:
            prev_row = self.client.fetchone(
                """
                SELECT dv.downloads_count, dv.api_calls_count, dv.views_count,
                       dv.reuses_count, dv.followers_count, dv.popularity_score,
                       dv.metadata_volatile, db.data as blob_data
                FROM dataset_versions dv
                JOIN dataset_blobs db ON dv.blob_id = db.id
                WHERE dv.dataset_id = %s
                ORDER BY dv.timestamp DESC LIMIT 1
                """,
                (str(params.dataset_id),),
            )
            if prev_row:
                # 1. Reconstruct full snapshots including metrics
                prev_snapshot = deep_merge(prev_row["blob_data"], prev_row["metadata_volatile"] or {})
                prev_comparable = prev_snapshot.copy()
                prev_comparable.update(
                    {
                        "downloads_count": prev_row["downloads_count"],
                        "api_calls_count": prev_row["api_calls_count"],
                        "views_count": prev_row["views_count"],
                        "reuses_count": prev_row["reuses_count"],
                        "followers_count": prev_row["followers_count"],
                        "popularity_score": prev_row["popularity_score"],
                    }
                )

                curr_snapshot = deep_merge(stripped, volatile)
                curr_comparable = curr_snapshot.copy()
                curr_comparable.update(
                    {
                        "downloads_count": params.downloads_count,
                        "api_calls_count": params.api_calls_count,
                        "views_count": params.views_count,
                        "reuses_count": params.reuses_count,
                        "followers_count": params.followers_count,
                        "popularity_score": params.popularity_score,
                    }
                )

                # 2. Compute diff on harmonized structures
                diff = calculate_snapshot_diff(prev_comparable, curr_comparable)

        data_str = json.dumps(stripped, sort_keys=True)
        stable_hash = hashlib.sha256(data_str.encode()).hexdigest()

        blob_row = self.client.fetchone(
            """
            INSERT INTO dataset_blobs (dataset_id, hash, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (dataset_id, hash)
            DO UPDATE SET id = dataset_blobs.id
            RETURNING id
            """,
            (str(params.dataset_id), stable_hash, Json(stripped)),
        )
        blob_id = blob_row["id"]

        self.client.execute(
            """
            INSERT INTO dataset_versions (
                dataset_id, blob_id, checksum, title, downloads_count, api_calls_count,
                views_count, reuses_count, followers_count, popularity_score, diff,
                metadata_volatile
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(params.dataset_id),
                str(blob_id),
                params.checksum,
                params.title,
                params.downloads_count,
                params.api_calls_count,
                params.views_count,
                params.reuses_count,
                params.followers_count,
                params.popularity_score,
                Json(diff) if diff else None,
                Json(volatile) if volatile else None,
            ),
        )

    def get_by_buid(self, dataset_buid: str) -> Dataset | None:
        row = self.client.fetchone(
            """
            SELECT d.*, dv.downloads_count, dv.api_calls_count, dv.views_count,
                   dv.reuses_count, dv.followers_count, dv.popularity_score,
                   dv.timestamp as last_version_timestamp, dv.checksum
            FROM datasets d
            LEFT JOIN LATERAL (
                SELECT downloads_count, api_calls_count, views_count,
                       reuses_count, followers_count, popularity_score, timestamp, checksum
                FROM dataset_versions
                WHERE dataset_id = d.id
                ORDER BY timestamp DESC
                LIMIT 1
            ) dv ON TRUE
            WHERE d.buid = %s
            """,
            (dataset_buid,),
        )
        if row:
            row["id"] = uuid.UUID(row["id"])
            return Dataset.from_dict(row)
        return None

    def get(self, dataset_id) -> Dataset:
        data = self.client.fetchone(
            """
            SELECT d.*,
            COALESCE(jsonb_agg(jsonb_build_object(
                'version_id', dv.id,
                'dataset_id', dv.dataset_id,
                'blob_id', dv.blob_id,
                'metadata_volatile', dv.metadata_volatile,
                'checksum', dv.checksum,
                'downloads_count', dv.downloads_count,
                'api_calls_count', dv.api_calls_count,
                'views_count', dv.views_count,
                'reuses_count', dv.reuses_count,
                'followers_count', dv.followers_count,
                'popularity_score', dv.popularity_score,
                'diff', dv.diff
            ) ORDER BY dv.timestamp), '[]'::jsonb) AS versions,
           (
               SELECT jsonb_build_object(
                              'downloads_count', dq.downloads_count,
                              'api_calls_count', dq.api_calls_count,
                              'has_description', dq.has_description,
                              'is_slug_valid', dq.is_slug_valid,
                              'evaluation_results', dq.evaluation_results
                          )
               FROM dataset_quality dq
               WHERE dq.dataset_id = d.id
               ORDER BY dq.timestamp DESC
               LIMIT 1
           ) AS quality
            FROM datasets d
            LEFT JOIN dataset_versions dv ON dv.dataset_id = d.id
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            JOIN dataset_quality dq ON d.id = dq.dataset_id
            WHERE d.id = %s
            GROUP BY d.id LIMIT 1;
            """,
            (str(dataset_id),),
        )
        data["id"] = uuid.UUID(data["id"])
        dataset = Dataset.from_dict(data)
        dataset.add_quality(**data["quality"])
        versions = self.client.fetchall(
            """
            SELECT dv.dataset_id, db.data as blob_data, dv.metadata_volatile, dv.snapshot,
                   dv.checksum, dv.downloads_count, dv.api_calls_count, dv.views_count,
                   dv.reuses_count, dv.followers_count, dv.popularity_score, dv.diff, dv.timestamp
            FROM dataset_versions dv
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            WHERE dv.dataset_id = %s;
            """,
            (str(dataset_id),),
        )

        for version_row in versions:
            # Reconstruct the full snapshot
            blob_data = version_row.pop("blob_data")
            volatile = version_row.pop("metadata_volatile")
            legacy_snapshot = version_row.pop("snapshot")  # For backward compatibility

            # Use legacy snapshot if blob_data is None (old data before migration)
            if blob_data is None and legacy_snapshot is not None:
                snapshot = legacy_snapshot
            else:
                snapshot = deep_merge(blob_data or {}, volatile or {})

            version_row["snapshot"] = snapshot
            version_row["metadata_volatile"] = volatile
            dataset.add_version(**version_row)

        return dataset

    def get_checksum_by_buid(self, dataset_buid) -> str or None:
        data = self.client.fetchone(
            """SELECT dv.checksum FROM dataset_versions dv JOIN datasets d ON d.id = dv.dataset_id WHERE d.buid = %s ORDER BY dv.timestamp DESC LIMIT 1""",
            (str(dataset_buid),),
        )
        if data is not None:
            return data.get("checksum", None)
        return

    def get_publishers_stats(self) -> list[dict[str, any]]:
        """Récupère les statistiques des publishers (nom et nombre de datasets)"""
        query = """
        SELECT publisher, COUNT(*) AS dataset_count
        FROM datasets
        WHERE publisher IS NOT NULL
        GROUP BY publisher
        ORDER BY publisher;
        """
        return self.client.fetchall(query) or []

    def get_id_by_slug(self, platform_id, slug):
        result = self.client.fetchone(
            """SELECT id FROM datasets WHERE platform_id = %s AND slug = %s; """,
            (str(platform_id), str(slug)),
        )
        return result["id"]

    def update_dataset_sync_status(self, platform_id, dataset_id, status):
        self.client.execute(
            """UPDATE datasets SET last_sync = now(), last_sync_status = %s WHERE platform_id = %s AND id = %s;""",
            (status, str(platform_id), str(dataset_id)),
        )

    def get_slugs(self, platform_id):
        result = [
            data["slug"]
            for data in self.client.fetchall(
                """SELECT slug FROM datasets WHERE platform_id = %s ORDER BY slug;""",
                (str(platform_id),),
            )
        ]
        return result

    def get_buids(self, platform_id):
        result = [
            data["buid"]
            for data in self.client.fetchall(
                """SELECT buid FROM datasets WHERE platform_id = %s;""",
                (str(platform_id),),
            )
        ]
        return result

    def update_dataset_state(self, dataset: Dataset) -> None:
        print(dataset.id, dataset.is_deleted)
        self.client.execute(
            """UPDATE datasets SET deleted = %s WHERE id = %s;""",
            (dataset.is_deleted, str(dataset.id)),
        )
