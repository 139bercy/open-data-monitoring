import uuid
from typing import Optional
from uuid import UUID
from psycopg2._json import Json

from domain.datasets.aggregate import Dataset
from domain.datasets.ports import AbstractDatasetRepository
from infrastructure.database.postgres import PostgresClient


class PostgresDatasetRepository(AbstractDatasetRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def add(self, dataset: Dataset) -> None:
        self.client.execute(
            """
            INSERT INTO datasets (
                id, platform_id, buid, slug, page, publisher, created, modified, published, restricted, deleted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                platform_id = EXCLUDED.platform_id,
                buid = EXCLUDED.buid,
                slug = EXCLUDED.slug,
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
                dataset.slug,
                dataset.page,
                dataset.publisher,
                dataset.created,
                dataset.modified,
                dataset.published,
                dataset.restricted,
                dataset.is_deleted,
            ),
        )
        self.client.execute(
            "INSERT INTO dataset_quality (dataset_id, downloads_count, api_calls_count, has_description) "
            "VALUES (%s, %s, %s, %s)"
            "ON CONFLICT (id) DO UPDATE SET "
            "downloads_count = EXCLUDED.downloads_count, "
            "api_calls_count = EXCLUDED.api_calls_count, "
            "has_description = EXCLUDED.has_description",
            (
                str(dataset.id),
                dataset.quality.downloads_count,
                dataset.quality.api_calls_count,
                dataset.quality.has_description,
            ),
        )

    def add_version(
        self,
        dataset_id: UUID,
        snapshot: dict,
        checksum: str,
        downloads_count: int,
        api_calls_count: int,
    ) -> None:
        self.client.execute(
            "INSERT INTO dataset_versions (dataset_id, snapshot, checksum, downloads_count, api_calls_count) VALUES (%s, %s, %s, %s, %s)",
            (
                str(dataset_id),
                Json(snapshot),
                checksum,
                downloads_count,
                api_calls_count,
            ),
        )

    def get_by_buid(self, dataset_buid: str) -> Optional[Dataset]:
        row = self.client.fetchone("SELECT * FROM datasets WHERE buid = %s", (dataset_buid,))
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
                'snapshot', dv.snapshot,
                'checksum', dv.checksum, 
                'downloads_count', dv.downloads_count, 
                'api_calls_count', dv.api_calls_count
            ) ORDER BY dv.timestamp), '[]'::jsonb) AS versions,
           (
               SELECT jsonb_build_object(
                              'downloads_count', dq.downloads_count,
                              'api_calls_count', dq.api_calls_count,
                              'has_description', dq.has_description
                          )
               FROM dataset_quality dq
               WHERE dq.dataset_id = d.id
               LIMIT 1
           ) AS quality
            FROM datasets d
            JOIN dataset_versions dv ON dv.dataset_id = d.id
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
            "SELECT dataset_id, snapshot, checksum, downloads_count, api_calls_count from dataset_versions WHERE dataset_id = %s;",
            (str(dataset_id),),
        )
        for version in versions:
            dataset.add_version(**version)
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
            (str(platform_id), slug),
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

