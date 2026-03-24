from __future__ import annotations

import hashlib
import json
import uuid
from uuid import UUID

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
    # Global top-level volatile fields
    global_volatile = _pop_fields(stripped, ["last_modified", "last_update", "expected_update", "quality"])
    volatile.update(global_volatile)

    # Harvest: Strip only specific timestamps inside, keep the rest (uri, remote_id)
    if "harvest" in stripped and isinstance(stripped["harvest"], dict):
        harvest = stripped["harvest"].copy()
        harvest_volatile = _pop_fields(harvest, ["last_update", "modified_at", "issued_at", "created_at", "valid_at"])
        if harvest_volatile:
            volatile.setdefault("harvest", {}).update(harvest_volatile)
        stripped["harvest"] = harvest

    # Resources: Strip only specific timestamps inside each resource, keep the rest
    if "resources" in stripped and isinstance(stripped["resources"], list):
        _strip_resources_volatile_fields(stripped, volatile)


def _strip_resources_volatile_fields(stripped: dict, volatile: dict) -> None:
    """Helper to strip volatile fields from resources list."""
    resources = []
    resources_volatile = []
    has_volatile = False

    for res in stripped["resources"]:
        res_copy, res_vol = _strip_single_resource_volatile_fields(res)
        resources.append(res_copy)
        resources_volatile.append(res_vol)
        if res_vol:
            has_volatile = True

    stripped["resources"] = resources
    if has_volatile:
        volatile["resources"] = resources_volatile

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


def _strip_single_resource_volatile_fields(res: dict | any) -> tuple[dict | any, dict]:
    """Helper to strip volatile fields from a single resource."""
    if not isinstance(res, dict):
        return res, {}

    res_copy = res.copy()
    # 1. Strip top-level volatile fields in resource
    res_vol = _pop_fields(res_copy, ["last_modified", "last_update", "created_at", "published"])

    # 2. Strip nested harvest fields in resource
    if "harvest" in res_copy and isinstance(res_copy["harvest"], dict):
        h_copy = res_copy["harvest"].copy()
        h_vol = _pop_fields(h_copy, ["last_update", "modified_at", "created_at"])
        if h_vol:
            res_vol.setdefault("harvest", {}).update(h_vol)
        res_copy["harvest"] = h_copy

    # 3. Strip volatile extras fields in resource (analysis:*, check:*)
    if "extras" in res_copy and isinstance(res_copy["extras"], dict):
        e_copy = res_copy["extras"].copy()
        e_keys_to_strip = [k for k in e_copy.keys() if k.startswith("analysis:") or k.startswith("check:")]
        e_vol = _pop_fields(e_copy, e_keys_to_strip)
        if e_vol:
            res_vol.setdefault("extras", {}).update(e_vol)
        res_copy["extras"] = e_copy

    return res_copy, res_vol


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


def _get_frequency_thresholds(frequency: str | None) -> int:
    """Mapping to days (including grace period) based on ODS frequency labels."""
    thresholds = {
        "daily": 2,
        "continuous": 2,
        "weekly": 9,
        "monthly": 37,
        "quarterly": 105,
        "semiannual": 210,
        "annual": 395,
        "punctual": 3650,
    }
    return thresholds.get(str(frequency).lower(), 90)


class PostgresDatasetRepository(AbstractDatasetRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def add(self, dataset: Dataset) -> None:
        self.client.execute(
            """
            INSERT INTO datasets (
                id, platform_id, buid, slug, title, page, publisher, created, modified, published, restricted, deleted, deleted_at, linked_dataset_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                deleted = EXCLUDED.deleted,
                deleted_at = EXCLUDED.deleted_at,
                linked_dataset_id = EXCLUDED.linked_dataset_id
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
                dataset.deleted_at,
                str(dataset.linked_dataset_id) if dataset.linked_dataset_id else None,
            ),
        )
        # Calculate health scores for persistence using Domain logic
        if dataset.quality and dataset.modified and not dataset.restricted and dataset.published is not False:
            dataset.calculate_health_scores()

        if dataset.quality:
            self.client.execute(
                "INSERT INTO dataset_quality (dataset_id, downloads_count, api_calls_count, has_description, is_slug_valid, evaluation_results, syntax_change_score, evaluated_blob_id, health_score, health_quality_score, health_freshness_score, health_engagement_score) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                "ON CONFLICT (dataset_id) DO UPDATE SET "
                "downloads_count = EXCLUDED.downloads_count, "
                "api_calls_count = EXCLUDED.api_calls_count, "
                "has_description = EXCLUDED.has_description, "
                "evaluation_results = COALESCE(EXCLUDED.evaluation_results, dataset_quality.evaluation_results), "
                "is_slug_valid = EXCLUDED.is_slug_valid, "
                "syntax_change_score = COALESCE(EXCLUDED.syntax_change_score, dataset_quality.syntax_change_score), "
                "evaluated_blob_id = COALESCE(EXCLUDED.evaluated_blob_id, dataset_quality.evaluated_blob_id), "
                "health_score = EXCLUDED.health_score, "
                "health_quality_score = EXCLUDED.health_quality_score, "
                "health_freshness_score = EXCLUDED.health_freshness_score, "
                "health_engagement_score = EXCLUDED.health_engagement_score",
                (
                    str(dataset.id),
                    dataset.quality.downloads_count,
                    dataset.quality.api_calls_count,
                    dataset.quality.has_description,
                    dataset.quality.is_slug_valid,
                    Json(dataset.quality.evaluation_results) if dataset.quality.evaluation_results else None,
                    dataset.quality.syntax_change_score,
                    str(dataset.quality.evaluated_blob_id) if dataset.quality.evaluated_blob_id else None,
                    dataset.quality.health_score,
                    dataset.quality.health_quality_score,
                    dataset.quality.health_freshness_score,
                    dataset.quality.health_engagement_score,
                ),
            )

    def add_version(self, params: DatasetVersionParams) -> None:
        """Add a new version of a dataset using Parameter Object pattern."""
        stripped, volatile = strip_volatile_fields(params.snapshot)
        if volatile is None:
            volatile = {}

        # Add metrics to volatile data for searchability without migration
        volatile["records_count"] = params.records_count
        volatile["size_bytes"] = params.size_bytes

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
                        "records_count": params.records_count,
                        "size_bytes": params.size_bytes,
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
                   dv.timestamp as last_version_timestamp, dv.checksum,
                   db.data as blob_data, dv.metadata_volatile, d.deleted_at
            FROM datasets d
            LEFT JOIN LATERAL (
                SELECT downloads_count, api_calls_count, views_count,
                       reuses_count, followers_count, popularity_score, timestamp, checksum,
                       blob_id, metadata_volatile
                FROM dataset_versions
                WHERE dataset_id = d.id
                ORDER BY timestamp DESC
                LIMIT 1
            ) dv ON TRUE
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            WHERE d.buid = %s
            """,
            (dataset_buid,),
        )
        if row:
            row["id"] = uuid.UUID(row["id"])
            # Reconstruct full raw metadata
            blob_data = row.pop("blob_data") or {}
            volatile = row.pop("metadata_volatile") or {}
            row["raw"] = deep_merge(blob_data, volatile)
            return Dataset.from_dict(row)
        return None

    def get(self, dataset_id: UUID, include_versions: bool = True) -> Dataset:
        data = self.client.fetchone(
            """
            SELECT d.*,
                   dq.has_description, dq.is_slug_valid, dq.evaluation_results, dq.evaluated_blob_id,
                   dq.downloads_count as q_downloads_count, dq.api_calls_count as q_api_calls_count,
                   dq.health_score, dq.health_quality_score, dq.health_freshness_score, dq.health_engagement_score, dq.syntax_change_score
             FROM datasets d
             LEFT JOIN (
                SELECT DISTINCT ON (dataset_id) dataset_id, has_description, is_slug_valid, evaluation_results, evaluated_blob_id, downloads_count, api_calls_count,
                       health_score, health_quality_score, health_freshness_score, health_engagement_score, syntax_change_score
                FROM dataset_quality
                ORDER BY dataset_id, timestamp DESC
             ) dq ON d.id = dq.dataset_id
             WHERE d.id = %s
             LIMIT 1;
            """,
            (str(dataset_id),),
        )

        if data is None:
            return None

        # Current snapshot reconstruction for the main aggregate
        cur_row = self.client.fetchone(
            """
            SELECT dv.metadata_volatile, db.data as blob_data,
                   dv.downloads_count, dv.api_calls_count, dv.views_count,
                   dv.reuses_count, dv.followers_count, dv.popularity_score,
                   dv.timestamp, dv.checksum
            FROM dataset_versions dv
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            WHERE dv.dataset_id = %s
            ORDER BY dv.timestamp DESC LIMIT 1
            """,
            (str(dataset_id),),
        )
        if cur_row:
            blob_data = cur_row.get("blob_data") or {}
            volatile = cur_row.get("metadata_volatile") or {}
            data["raw"] = deep_merge(blob_data, volatile)
            # Update metrics in the data dict before from_dict
            data.update(
                {
                    "downloads_count": cur_row.get("downloads_count"),
                    "api_calls_count": cur_row.get("api_calls_count"),
                    "views_count": cur_row.get("views_count"),
                    "reuses_count": cur_row.get("reuses_count"),
                    "followers_count": cur_row.get("followers_count"),
                    "popularity_score": cur_row.get("popularity_score"),
                    "records_count": cur_row.get("records_count")
                    or (blob_data.get("metas", {}).get("default", {}).get("records_count")),
                    "size_bytes": cur_row.get("size_bytes") or blob_data.get("records_size"),
                    "last_version_timestamp": cur_row.get("timestamp"),
                    "checksum": cur_row.get("checksum"),
                }
            )

        data["id"] = uuid.UUID(data["id"])
        dataset = Dataset.from_dict(data)

        # Add quality if present (may be None for datasets without quality records)
        # Add quality if present (checked via has_description or other indicators)
        if data.get("has_description") is not None:
            dataset.add_quality(
                downloads_count=data.get("q_downloads_count"),
                api_calls_count=data.get("q_api_calls_count"),
                has_description=data.get("has_description"),
                is_slug_valid=data.get("is_slug_valid", True),
                evaluation_results=data.get("evaluation_results"),
                syntax_change_score=data.get("syntax_change_score"),
                evaluated_blob_id=data.get("evaluated_blob_id"),
                health_score=data.get("health_score"),
                health_quality_score=data.get("health_quality_score"),
                health_freshness_score=data.get("health_freshness_score"),
                health_engagement_score=data.get("health_engagement_score"),
            )

        if not include_versions:
            # Still populate identifying metadata for the aggregate from latest version if exists
            if cur_row:
                # We need checksum and last_version_timestamp for the aggregate
                latest_info = self.client.fetchone(
                    "SELECT timestamp, checksum FROM dataset_versions WHERE dataset_id = %s ORDER BY timestamp DESC LIMIT 1",
                    (str(dataset_id),),
                )
                if latest_info:
                    dataset.last_version_timestamp = latest_info["timestamp"]
                    dataset.checksum = latest_info["checksum"]
            return dataset

        versions = self.client.fetchall(
            """
            SELECT dv.dataset_id, dv.blob_id, db.data as blob_data, dv.metadata_volatile,
                   dv.checksum, dv.downloads_count, dv.api_calls_count, dv.views_count,
                   dv.reuses_count, dv.followers_count, dv.popularity_score, dv.diff, dv.timestamp
            FROM dataset_versions dv
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            WHERE dv.dataset_id = %s
            ORDER BY dv.timestamp ASC;
            """,
            (str(dataset_id),),
        )

        for version_row in versions:
            # Reconstruct the full snapshot
            blob_data = version_row.pop("blob_data")
            volatile = version_row.pop("metadata_volatile")

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

    def get_id_by_slug(self, platform_id: UUID, slug: str) -> UUID | None:
        result = self.client.fetchone(
            """SELECT id FROM datasets WHERE platform_id = %s AND slug = %s; """,
            (str(platform_id), str(slug)),
        )
        return UUID(result["id"]) if result else None

    def get_id_by_slug_globally(self, slug: str, exclude_id: UUID | None = None) -> UUID | None:
        query = "SELECT id FROM datasets WHERE slug = %s"
        params = [str(slug)]

        if exclude_id:
            query += " AND id != %s"
            params.append(str(exclude_id))

        query += " LIMIT 1;"

        result = self.client.fetchone(query, tuple(params))
        if result:
            return UUID(result["id"])

        # Fallback: if slug has a numeric suffix like '-12345', try without it
        # This is common in DataGouv URLs
        if "-" in slug:
            parts = slug.rsplit("-", 1)
            if parts[1].isdigit():
                clean_slug = parts[0]

                query_fallback = "SELECT id FROM datasets WHERE slug = %s"
                params_fallback = [str(clean_slug)]

                if exclude_id:
                    query_fallback += " AND id != %s"
                    params_fallback.append(str(exclude_id))

                query_fallback += " LIMIT 1;"

                result = self.client.fetchone(query_fallback, tuple(params_fallback))
                if result:
                    return UUID(result["id"])

        return None

    def update_linking(self, dataset: Dataset) -> None:
        self.client.execute(
            """UPDATE datasets SET linked_dataset_id = %s WHERE id = %s;""",
            (str(dataset.linked_dataset_id) if dataset.linked_dataset_id else None, str(dataset.id)),
        )

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
        self.client.execute(
            """UPDATE datasets SET deleted = %s, deleted_at = %s WHERE id = %s;""",
            (dataset.is_deleted, dataset.deleted_at, str(dataset.id)),
        )

    def search(
        self,
        platform_id: str | None = None,
        publisher: str | None = None,
        q: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        modified_from: str | None = None,
        modified_to: str | None = None,
        is_deleted: bool | None = None,
        sort_by: str = "modified",
        order: str = "desc",
        page: int = 1,
        page_size: int = 25,
        min_health: float | None = None,
        max_health: float | None = None,
        include_cold_storage: bool = False,
    ) -> tuple[list[dict], int]:
        """Search datasets with filters, sorting and pagination."""
        where_sql, params = self._build_where_clause(
            platform_id,
            publisher,
            q,
            created_from,
            created_to,
            modified_from,
            modified_to,
            is_deleted,
            min_health=min_health,
            max_health=max_health,
            include_cold_storage=include_cold_storage,
        )

        # Count total
        count_query = f"SELECT COUNT(*) AS cnt FROM datasets d WHERE {where_sql}"
        total_rows = self.client.fetchall(count_query, tuple(params))
        total = int(total_rows[0]["cnt"]) if total_rows else 0

        # Build sorting
        order_sql, sort_dir = self._build_order_clause(sort_by, order)

        # Pagination
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size

        # Main query
        list_query = f"""
            WITH latest_versions AS (
                SELECT DISTINCT ON (dataset_id) dataset_id, title, blob_id, downloads_count, api_calls_count, views_count, reuses_count, followers_count, popularity_score, metadata_volatile, timestamp
                FROM dataset_versions
                ORDER BY dataset_id, timestamp DESC
            ),
            version_counts AS (
                SELECT dataset_id, COUNT(*) AS versions_count
                FROM dataset_versions
                GROUP BY dataset_id
            ),
            latest_quality AS (
                SELECT DISTINCT ON (dataset_id) dataset_id, has_description, is_slug_valid, evaluation_results, syntax_change_score, evaluated_blob_id,
                       health_score, health_quality_score, health_freshness_score, health_engagement_score
                FROM dataset_quality
                ORDER BY dataset_id, timestamp DESC
            )
            SELECT d.id,
                   d.platform_id,
                   d.buid,
                   d.slug,
                   d.publisher,
                   d.page,
                   d.created,
                   d.modified,
                   d.restricted,
                   d.published,
                   COALESCE(
                       lv.title,
                       (db.data ->> 'title'),
                       (db.data -> 'metas' -> 'default' ->> 'title'),
                       d.slug
                   ) AS title,
                   lv.timestamp AS timestamp,
                   lv.api_calls_count AS api_calls_count,
                   lv.downloads_count AS downloads_count,
                   lv.views_count AS views_count,
                   lv.reuses_count AS reuses_count,
                   lv.followers_count AS followers_count,
                   COALESCE(
                       (lv.metadata_volatile ->> 'records_count')::int,
                       (db.data ->> 'records_count')::int,
                       (db.data -> 'metas' -> 'default' ->> 'records_count')::int
                   ) AS records_count,
                   COALESCE(
                       (lv.metadata_volatile ->> 'size_bytes')::bigint,
                       (db.data ->> 'records_size')::bigint,
                       (db.data -> 'metas' -> 'default' ->> 'records_size')::bigint
                   ) AS size_bytes,
                   COALESCE(vc.versions_count, 0) AS versions_count,
                   d.last_sync,
                   d.last_sync_status,
                   d.deleted,
                   d.linked_dataset_id,
                   ld.slug AS linked_dataset_slug,
                   lp.name AS linked_platform_name,
                   dq.has_description as has_description,
                   dq.is_slug_valid as is_slug_valid,
                   dq.evaluation_results as evaluation_results,
                   dq.syntax_change_score as syntax_change_score,
                   dq.evaluated_blob_id as evaluated_blob_id,
                   dq.health_score as stored_health_score,
                   dq.health_quality_score as stored_quality_score,
                   dq.health_freshness_score as stored_freshness_score,
                   dq.health_engagement_score as stored_engagement_score,
                   lv.blob_id as current_blob_id,
                   db.data as data

            FROM datasets d
            LEFT JOIN latest_versions lv ON lv.dataset_id = d.id
            LEFT JOIN dataset_blobs db ON lv.blob_id = db.id
            LEFT JOIN version_counts vc ON vc.dataset_id = d.id
            LEFT JOIN latest_quality dq ON d.id = dq.dataset_id
            LEFT JOIN datasets ld ON d.linked_dataset_id = ld.id
            LEFT JOIN platforms lp ON ld.platform_id = lp.id

            WHERE {where_sql}
            ORDER BY {order_sql} {sort_dir}
            LIMIT %s OFFSET %s
        """
        list_params = params + [page_size, offset]
        rows = self.client.fetchall(list_query, tuple(list_params))

        items = []
        for r in rows:
            health_scores = {
                "global": r.get("stored_health_score"),
                "quality": r.get("stored_quality_score"),
                "freshness": r.get("stored_freshness_score"),
                "engagement": r.get("stored_engagement_score"),
            }

            items.append(
                {
                    "id": r["id"],
                    "platform_id": r["platform_id"],
                    "buid": r.get("buid"),
                    "slug": r.get("slug"),
                    "publisher": r.get("publisher"),
                    "title": r.get("title"),
                    "timestamp": r["timestamp"].isoformat() if r.get("timestamp") else None,
                    "created": r["created"].isoformat() if r.get("created") else None,
                    "modified": r["modified"].isoformat() if r.get("modified") else None,
                    "restricted": r.get("restricted"),
                    "published": r.get("published"),
                    "downloads_count": r.get("downloads_count"),
                    "api_calls_count": r.get("api_calls_count"),
                    "views_count": r.get("views_count"),
                    "reuses_count": r.get("reuses_count"),
                    "followers_count": r.get("followers_count"),
                    "popularity_score": r.get("popularity_score"),
                    "records_count": r.get("records_count"),
                    "size_bytes": r.get("size_bytes"),
                    "versions_count": r.get("versions_count"),
                    "page": r.get("page"),
                    "last_sync": r.get("last_sync"),
                    "last_sync_status": r.get("last_sync_status"),
                    "deleted": r.get("deleted"),
                    "linked_dataset_id": r.get("linked_dataset_id"),
                    "linked_dataset_slug": r.get("linked_dataset_slug"),
                    "linked_platform_name": r.get("linked_platform_name"),
                    "quality": {
                        "has_description": r.get("has_description"),
                        "is_slug_valid": r.get("is_slug_valid"),
                        "evaluation_results": r.get("evaluation_results"),
                        "syntax_change_score": r.get("syntax_change_score"),
                        "evaluated_blob_id": r.get("evaluated_blob_id"),
                    },
                    "current_snapshot": {
                        "id": r.get("id"),
                        "blob_id": r.get("current_blob_id"),
                        "timestamp": r.get("timestamp"),
                    },
                    "health_score": health_scores["global"],
                    "health_quality_score": health_scores["quality"],
                    "health_freshness_score": health_scores["freshness"],
                    "health_engagement_score": health_scores["engagement"],
                }
            )

        return items, total

    def _build_where_clause(
        self,
        platform_id: str | None,
        publisher: str | None,
        q: str | None,
        created_from: str | None,
        created_to: str | None,
        modified_from: str | None,
        modified_to: str | None,
        is_deleted: bool | None,
        min_health: float | None = None,
        max_health: float | None = None,
        include_cold_storage: bool = False,
    ) -> tuple[str, list]:
        """Build WHERE clause and params for dataset filtering."""
        where_clauses = ["TRUE"]
        params: list = []

        if platform_id:
            where_clauses.append("d.platform_id = %s")
            params.append(platform_id)
        if publisher:
            if publisher == "Inconnu":
                where_clauses.append("(d.publisher IS NULL OR d.publisher = '' OR d.publisher = 'Inconnu')")
            else:
                where_clauses.append("d.publisher = %s")
                params.append(publisher)
        if q:
            where_clauses.append("d.slug ILIKE %s")
            params.append(f"%{q}%")

        self._add_date_filters(where_clauses, params, created_from, created_to, modified_from, modified_to)

        if is_deleted is not None:
            where_clauses.append("d.deleted = %s")
            params.append(is_deleted)
        elif not include_cold_storage:
            # Default behavior: hide datasets deleted more than 30 days ago
            where_clauses.append("(d.deleted = FALSE OR d.deleted_at > NOW() - INTERVAL '30 days')")

        if min_health is not None:
            where_clauses.append("dq.health_score >= %s")
            params.append(min_health)
        if max_health is not None:
            where_clauses.append("dq.health_score <= %s")
            params.append(max_health)

        return " AND ".join(where_clauses), params

    def _add_date_filters(self, where_clauses, params, c_from, c_to, m_from, m_to):
        if c_from:
            where_clauses.append("d.created >= %s")
            params.append(c_from)
        if c_to:
            where_clauses.append("d.created <= %s")
            params.append(c_to)
        if m_from:
            where_clauses.append("d.modified >= %s")
            params.append(m_from)
        if m_to:
            where_clauses.append("d.modified <= %s")
            params.append(m_to)

    def _build_order_clause(self, sort_by: str, order: str) -> tuple[str, str]:
        """Build ORDER BY clause with NULL-safe sorting."""
        sort_column = self._get_sort_column(sort_by)
        order_sql = self._get_order_sql(sort_column)
        sort_dir = "DESC" if order.lower() != "asc" else "ASC"

        # Add NULLS LAST for specific columns like health_score and size metrics
        if sort_column in ("health_score", "size_bytes", "records_count"):
            sort_dir += " NULLS LAST"

        return order_sql, sort_dir

    def _get_sort_column(self, sort_by: str) -> str:
        valid = (
            "created",
            "modified",
            "publisher",
            "title",
            "api_calls_count",
            "downloads_count",
            "versions_count",
            "popularity_score",
            "views_count",
            "reuses_count",
            "followers_count",
            "health_score",
            "size_bytes",
            "records_count",
        )
        return sort_by if sort_by in valid else "modified"

    def _get_order_sql(self, sort_column: str) -> str:
        mapping = {
            "title": "COALESCE(title, '')",
            "api_calls_count": "COALESCE(lv.api_calls_count, 0)",
            "downloads_count": "COALESCE(lv.downloads_count, 0)",
            "versions_count": "COALESCE(vc.versions_count, 0)",
            "popularity_score": "COALESCE(lv.popularity_score, 0)",
            "views_count": "COALESCE(lv.views_count, 0)",
            "reuses_count": "COALESCE(lv.reuses_count, 0)",
            "followers_count": "COALESCE(lv.followers_count, 0)",
            "publisher": "COALESCE(publisher, '')",
            "health_score": "dq.health_score",
            "size_bytes": "size_bytes",
            "records_count": "records_count",
        }
        return mapping.get(sort_column, sort_column)

    def list_publishers(self, platform_id: UUID | None = None, q: str | None = None, limit: int = 50) -> list[str]:
        """Get a list of distinct publishers, optionally filtered by platform or name."""
        where_clauses = ["publisher IS NOT NULL"]
        params: list = []

        if platform_id is not None:
            where_clauses.append("platform_id = %s")
            params.append(str(platform_id))

        if q:
            where_clauses.append("publisher ILIKE %s")
            params.append(f"%{q}%")

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT publisher
            FROM datasets
            WHERE {where_sql}
            GROUP BY publisher
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        params.append(limit)

        rows = self.client.fetchall(query, tuple(params))
        return [r["publisher"] for r in rows if r.get("publisher")]

    def get_detail(self, dataset_id: uuid.UUID, include_snapshots: bool = False) -> dict | None:
        """Get full dataset details including current snapshot and optionally history."""
        # Base dataset
        ds_query = """
            SELECT d.id, d.platform_id, d.buid, d.slug, d.page, d.publisher, d.created, d.modified, d.published, d.restricted, d.deleted, d.last_sync, d.last_sync_status, d.linked_dataset_id,
                   dq.has_description, dq.is_slug_valid, dq.evaluation_results, dq.syntax_change_score, dq.evaluated_blob_id,
                   dq.health_score, dq.health_quality_score, dq.health_freshness_score, dq.health_engagement_score,
                   ld.slug AS linked_dataset_slug,
                   lp.name AS linked_platform_name
            FROM datasets d
            LEFT JOIN (
                SELECT DISTINCT ON (dataset_id) dataset_id, has_description, is_slug_valid, evaluation_results, syntax_change_score, evaluated_blob_id,
                       health_score, health_quality_score, health_freshness_score, health_engagement_score
                FROM dataset_quality
                ORDER BY dataset_id, timestamp DESC
            ) dq ON d.id = dq.dataset_id
            LEFT JOIN datasets ld ON d.linked_dataset_id = ld.id
            LEFT JOIN platforms lp ON ld.platform_id = lp.id
            WHERE d.id = %s
        """
        rows = self.client.fetchall(ds_query, (str(dataset_id),))
        if not rows:
            return None
        d = rows[0]

        # Current snapshot
        cur_query = """
            SELECT dv.id, dv.blob_id, dv.timestamp, dv.downloads_count, dv.api_calls_count, dv.views_count, dv.reuses_count, dv.followers_count, dv.popularity_score, dv.metadata_volatile, db.data as blob_data, dv.title,
                   COALESCE(dv.title, db.data ->> 'title', db.data -> 'metas' -> 'default' ->> 'title') AS derived_title,
                   COALESCE(
                       (dv.metadata_volatile ->> 'records_count')::int,
                       (db.data ->> 'records_count')::int,
                       (db.data -> 'metas' -> 'default' ->> 'records_count')::int
                   ) AS records_count,
                   COALESCE(
                       (dv.metadata_volatile ->> 'size_bytes')::bigint,
                       (db.data ->> 'records_size')::bigint,
                       (db.data -> 'metas' -> 'default' ->> 'records_size')::bigint
                   ) AS size_bytes
            FROM dataset_versions dv
            LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
            WHERE dv.dataset_id = %s ORDER BY dv.timestamp DESC LIMIT 1
        """
        cur_rows = self.client.fetchall(cur_query, (str(dataset_id),))
        current_snapshot = None
        if cur_rows:
            r = cur_rows[0]
            snapshot_data = deep_merge(r.get("blob_data") or {}, r.get("metadata_volatile") or {})
            current_snapshot = {
                "id": r["id"],
                "blob_id": r["blob_id"],
                "timestamp": r["timestamp"],
                "downloads_count": r.get("downloads_count"),
                "api_calls_count": r.get("api_calls_count"),
                "views_count": r.get("views_count"),
                "reuses_count": r.get("reuses_count"),
                "followers_count": r.get("followers_count"),
                "popularity_score": r.get("popularity_score"),
                "records_count": r.get("records_count"),
                "size_bytes": r.get("size_bytes"),
                "title": r.get("derived_title"),
                "data": snapshot_data,
            }

        # Optional snapshots list
        snapshots = None
        if include_snapshots:
            list_rows = self.client.fetchall(
                """
                SELECT dv.id, dv.blob_id, dv.timestamp, dv.downloads_count, dv.api_calls_count, dv.views_count, dv.reuses_count, dv.followers_count, dv.popularity_score, dv.metadata_volatile, db.data as blob_data,
                       COALESCE(dv.title, db.data ->> 'title', db.data -> 'metas' -> 'default' ->> 'title') AS derived_title
                FROM dataset_versions dv
                LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
                WHERE dv.dataset_id = %s ORDER BY dv.timestamp DESC LIMIT 50
                """,
                (str(dataset_id),),
            )
            snapshots = [
                {
                    "id": r["id"],
                    "blob_id": r["blob_id"],
                    "timestamp": r["timestamp"],
                    "downloads_count": r.get("downloads_count"),
                    "api_calls_count": r.get("api_calls_count"),
                    "views_count": r.get("views_count"),
                    "reuses_count": r.get("reuses_count"),
                    "followers_count": r.get("followers_count"),
                    "popularity_score": r.get("popularity_score"),
                    "title": r.get("derived_title"),
                    "data": deep_merge(r.get("blob_data") or {}, r.get("metadata_volatile") or {}),
                }
                for r in list_rows
            ]

        health_scores = {
            "global": d.get("health_score"),
            "quality": d.get("health_quality_score"),
            "freshness": d.get("health_freshness_score"),
            "engagement": d.get("health_engagement_score"),
        }

        return {
            "id": d["id"],
            "platform_id": d["platform_id"],
            "publisher": d.get("publisher"),
            "title": current_snapshot.get("title") if current_snapshot else d["slug"],
            "buid": d["buid"],
            "slug": d["slug"],
            "page": d.get("page"),
            "created": d["created"],
            "modified": d["modified"],
            "published": d.get("published"),
            "restricted": d.get("restricted"),
            "deleted": d.get("deleted"),
            "last_sync": d.get("last_sync"),
            "last_sync_status": d.get("last_sync_status"),
            "linked_dataset_id": d.get("linked_dataset_id"),
            "linked_dataset_slug": d.get("linked_dataset_slug"),
            "linked_platform_name": d.get("linked_platform_name"),
            "quality": {
                "has_description": d.get("has_description"),
                "is_slug_valid": d.get("is_slug_valid"),
                "evaluation_results": d.get("evaluation_results"),
                "syntax_change_score": d.get("syntax_change_score"),
                "evaluated_blob_id": d.get("evaluated_blob_id"),
            },
            "current_snapshot": current_snapshot,
            "snapshots": snapshots,
            "records_count": current_snapshot.get("records_count") if current_snapshot else None,
            "size_bytes": current_snapshot.get("size_bytes") if current_snapshot else None,
            "health_breakdown": health_scores,
            "health_score": health_scores["global"] if health_scores else None,
            "health_quality_score": health_scores["quality"] if health_scores else None,
            "health_freshness_score": health_scores["freshness"] if health_scores else None,
            "health_engagement_score": health_scores["engagement"] if health_scores else None,
        }

    def get_versions(
        self, dataset_id: uuid.UUID, page: int = 1, page_size: int = 50, include_data: bool = False
    ) -> tuple[list[dict], int]:
        """Get paginated version history for a dataset."""
        offset = (max(1, page) - 1) * page_size

        cnt_rows = self.client.fetchall(
            "SELECT COUNT(*) AS cnt FROM dataset_versions WHERE dataset_id = %s",
            (str(dataset_id),),
        )
        total = int(cnt_rows[0]["cnt"]) if cnt_rows else 0

        if include_data:
            rows = self.client.fetchall(
                """
                SELECT dv.id, dv.blob_id, dv.timestamp, dv.downloads_count, dv.api_calls_count, dv.views_count, dv.reuses_count, dv.followers_count, dv.popularity_score, dv.diff, dv.metadata_volatile, db.data as blob_data,
                       COALESCE(dv.title, db.data ->> 'title', db.data -> 'metas' -> 'default' ->> 'title') AS derived_title
                FROM dataset_versions dv
                LEFT JOIN dataset_blobs db ON dv.blob_id = db.id
                WHERE dv.dataset_id = %s ORDER BY dv.timestamp DESC LIMIT %s OFFSET %s
                """,
                (str(dataset_id), page_size, offset),
            )
        else:
            rows = self.client.fetchall(
                """
                SELECT dv.id, dv.blob_id, dv.timestamp, dv.downloads_count, dv.api_calls_count, dv.views_count, dv.reuses_count, dv.followers_count, dv.popularity_score, dv.diff, dv.metadata_volatile, NULL as blob_data,
                       dv.title AS derived_title
                FROM dataset_versions dv
                WHERE dv.dataset_id = %s ORDER BY dv.timestamp DESC LIMIT %s OFFSET %s
                """,
                (str(dataset_id), page_size, offset),
            )

        items = [
            {
                "id": r["id"],
                "blob_id": r["blob_id"],
                "timestamp": r["timestamp"],
                "downloads_count": r.get("downloads_count"),
                "api_calls_count": r.get("api_calls_count"),
                "views_count": r.get("views_count"),
                "reuses_count": r.get("reuses_count"),
                "followers_count": r.get("followers_count"),
                "popularity_score": r.get("popularity_score"),
                "title": r.get("derived_title"),
                "diff": r.get("diff"),
                "data": (
                    deep_merge(r.get("blob_data") or {}, r.get("metadata_volatile") or {}) if include_data else None
                ),
            }
            for r in rows
        ]

        return items, total

    def refresh_materialized_views(self) -> None:
        """Refresh all materialized views used for analytics."""
        self.client.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY direction_health_stats_view")
