import hashlib
import json
import uuid
from typing import Optional
from uuid import UUID

from psycopg2.extras import Json

from logger import logger
from common import JsonSerializer, calculate_snapshot_diff
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import AbstractDatasetRepository
from infrastructure.database.postgres import PostgresClient


def strip_volatile_fields(data: dict) -> tuple[dict, dict]:
    """
    Removes fields that change frequently and returns them separately.
    Returns (stripped_data, volatile_data).
    """
    if not data:
        return data, {}
        
    stripped = data.copy()
    volatile = {}

    # ODS root fields
    volatile_ods = [
        "updated_at",
        "data_processed",
        "metadata_processed",
        "api_call_count",
        "download_count",
        "popularity_score",
        "attachment_download_count",
        "file_field_download_count",
        "records_size",
    ]
    for key in volatile_ods:
        if key in stripped:
            volatile[key] = stripped.pop(key)

    # ODS metas.default fields
    if "metas" in stripped and "default" in stripped["metas"]:
        default = stripped["metas"]["default"].copy()
        metas_default_volatile = {}
        for key in ["data_processed", "metadata_processed"]:
            if key in default:
                metas_default_volatile[key] = default.pop(key)
        
        if metas_default_volatile:
            if "metas" not in volatile:
                volatile["metas"] = {}
            volatile["metas"]["default"] = metas_default_volatile
            
        stripped["metas"] = stripped["metas"].copy()
        stripped["metas"]["default"] = default

    # DataGouv & common metrics
    if "metrics" in stripped:
        metrics_to_strip = ["views", "reuses", "followers", "datasets", "resources_downloads", "reuses_by_months", "followers_by_months"]
        if isinstance(stripped["metrics"], dict):
            new_metrics = stripped["metrics"].copy()
            metrics_volatile = {}
            for k in metrics_to_strip:
                if k in new_metrics:
                    metrics_volatile[k] = new_metrics.pop(k)
            
            if metrics_volatile:
                volatile["metrics"] = metrics_volatile
            stripped["metrics"] = new_metrics

    # Global volatile timestamps/metadata
    for k in ["last_modified", "last_update", "expected_update", "quality", "harvest", "resources"]:
        if k in stripped:
            volatile[k] = stripped.pop(k)

    # Internal flags
    if "internal" in stripped:
        internal = stripped["internal"].copy()
        internal_volatile = {}
        for k in ["last_modified_internal", "metadata_source_language", "catalog_site_contact", "last_update_internal"]:
            if k in internal:
                internal_volatile[k] = internal.pop(k)
        
        if internal_volatile:
            if "internal" not in volatile:
                volatile["internal"] = {}
            volatile["internal"].update(internal_volatile)
        stripped["internal"] = internal

    return stripped, volatile


def deep_merge(base: dict, volatile: dict) -> dict:
    """Deep merges volatile data back into base snapshot."""
    if not volatile:
        return base
        
    result = base.copy()
    for key, value in volatile.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


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

    def add_version(
        self,
        dataset_id: UUID,
        snapshot: dict,
        checksum: str,
        title: str,
        downloads_count: Optional[int] = None,
        api_calls_count: Optional[int] = None,
        views_count: Optional[int] = None,
        reuses_count: Optional[int] = None,
        followers_count: Optional[int] = None,
        popularity_score: Optional[float] = None,
        diff: Optional[dict] = None,
    ) -> None:
        # 1. Deduplicate the static metadata (blob)
        # We strip volatile fields to have a stable hash for the heavy metadata
        stripped, volatile = strip_volatile_fields(snapshot)
        
        # 2. Calculate diff against previous version if not provided
        if not diff:
            prev_row = self.client.fetchone(
                """
                SELECT dv.downloads_count, dv.api_calls_count, dv.views_count, 
                       dv.reuses_count, dv.followers_count, dv.popularity_score,
                       db.data as blob_data
                FROM dataset_versions dv 
                JOIN dataset_blobs db ON dv.blob_id = db.id 
                WHERE dv.dataset_id = %s 
                ORDER BY dv.timestamp DESC LIMIT 1
                """,
                (str(dataset_id),),
            )
            if prev_row:
                # Reconstruct "comparable" dicts including metrics
                prev_comparable = prev_row["blob_data"].copy()
                prev_comparable.update({
                    "downloads_count": prev_row["downloads_count"],
                    "api_calls_count": prev_row["api_calls_count"],
                    "views_count": prev_row["views_count"],
                    "reuses_count": prev_row["reuses_count"],
                    "followers_count": prev_row["followers_count"],
                    "popularity_score": prev_row["popularity_score"],
                })
                
                curr_comparable = stripped.copy()
                curr_comparable.update({
                    "downloads_count": downloads_count,
                    "api_calls_count": api_calls_count,
                    "views_count": views_count,
                    "reuses_count": reuses_count,
                    "followers_count": followers_count,
                    "popularity_score": popularity_score,
                })
                
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
            (str(dataset_id), stable_hash, Json(stripped)),
        )
        blob_id = blob_row["id"]

        # 2. Add the version referencing the blob
        self.client.execute(
            """
            INSERT INTO dataset_versions (
                dataset_id, blob_id, checksum, title, downloads_count, api_calls_count, 
                views_count, reuses_count, followers_count, popularity_score, diff,
                metadata_volatile
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(dataset_id),
                str(blob_id),
                checksum,
                title,
                downloads_count,
                api_calls_count,
                views_count,
                reuses_count,
                followers_count,
                popularity_score,
                Json(diff) if diff else None,
                Json(volatile) if volatile else None,
            ),
        )

    def get_by_buid(self, dataset_buid: str) -> Optional[Dataset]:
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
                'snapshot', COALESCE(dv.snapshot, db.data), -- Fallback for migrated data
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
            SELECT dv.dataset_id, dv.snapshot, db.data as blob_data, dv.metadata_volatile,
                   dv.checksum, dv.downloads_count, dv.api_calls_count, dv.views_count, 
                   dv.reuses_count, dv.followers_count, dv.popularity_score, dv.diff
            FROM dataset_versions dv
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            WHERE dv.dataset_id = %s;
            """,
            (str(dataset_id),),
        )
        for version_row in versions:
            # Reconstruct the full snapshot
            legacy_snapshot = version_row.pop("snapshot")
            blob_data = version_row.pop("blob_data")
            volatile = version_row.pop("metadata_volatile")
            
            if legacy_snapshot:
                snapshot = legacy_snapshot
            elif blob_data:
                snapshot = deep_merge(blob_data, volatile or {})
            else:
                snapshot = {}
            
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
            f"""SELECT id FROM datasets WHERE platform_id = %s AND slug = %s; """,
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
