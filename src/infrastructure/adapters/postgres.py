import uuid
from typing import Optional

from psycopg2.extras import Json

from application.dtos.dataset import DatasetRawDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository
from infrastructure.database.postgres import PostgresClient


class PostgresPlatformRepository(PlatformRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def save(self, platform: Platform) -> None:
        self.client.execute(
            """INSERT INTO platforms (
                id, name, slug, type, url, organization_id, key, datasets_count, last_sync
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                str(platform.id),
                platform.name,
                platform.slug,
                platform.type,
                platform.url,
                platform.organization_id,
                platform.key,
                platform.datasets_count,
                platform.last_sync,
            ),
        )

    def get(self, platform_id: uuid.UUID) -> Optional[Platform]:
        query = """
        SELECT 
            p.*,
            json_agg(
                json_build_object(
                    'platform_id', h.platform_id,
                    'timestamp', h.timestamp,
                    'status', h.status,
                    'datasets_count', h.datasets_count
                )
            ) FILTER (WHERE h.platform_id IS NOT NULL) AS syncs
        FROM platforms p
        LEFT JOIN platform_sync_histories h ON p.id = h.platform_id
        WHERE p.id = %s
        GROUP BY p.id;
        """
        row = self.client.fetchone(query, (str(platform_id),))
        if not row:
            return None
        row["id"] = uuid.UUID(row["id"])
        platform = Platform(**{k: v for k, v in row.items() if k != "syncs"})
        if row["syncs"]:
            for sync in row["syncs"]:
                platform.add_sync(sync)
        return platform

    def get_by_domain(self, domain) -> Platform:
        query = "SELECT * FROM platforms WHERE position(%s in url) > 0;"
        row = self.client.fetchone(query=query, params=(domain,))
        row["id"] = uuid.UUID(row["id"])
        return Platform(**{k: v for k, v in row.items()})

    def save_sync(self, platform_id, payload):
        self.client.execute(
            """UPDATE platforms SET datasets_count = %s, last_sync = %s WHERE id = %s;""",
            (payload["datasets_count"], payload["timestamp"], str(platform_id)),
        )
        self.client.execute(
            """INSERT INTO platform_sync_histories (platform_id, timestamp, status, datasets_count) VALUES (%s, %s, %s, %s)""",
            (
                str(platform_id),
                payload["timestamp"],
                payload["status"],
                payload["datasets_count"],
            ),
        )

    def all(self):
        return self.client.fetchall("""SELECT * from platforms;""")


class PostgresDatasetRepository(DatasetRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def add(self, dataset: Dataset) -> None:
        try:
            self.client.execute(
                """INSERT INTO datasets (id, platform_id, buid, slug, page, publisher, created, modified, published, restricted)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                ),
            )
        except Exception as e:
            print(e)
        finally:
            self.client.execute(
                """INSERT INTO dataset_versions (dataset_id, snapshot, checksum) VALUES (%s, %s, %s)""",
                (str(dataset.id), Json(dataset.raw), dataset.checksum),
            )

    def get(self, dataset_id) -> Dataset:
        data = self.client.fetchone(
            """
            SELECT d.*, COALESCE(jsonb_agg(jsonb_build_object(
                'dataset_id', dv.dataset_id,
                'snapshot', dv.snapshot,
                'checksum', dv.checksum
            ) ORDER BY dv.timestamp), '[]'::jsonb) AS versions
            FROM datasets d
            LEFT JOIN dataset_versions dv ON dv.dataset_id = d.id
            WHERE d.id = %s 
            GROUP BY d.id;
            """,
            (str(dataset_id),),
        )
        data["versions"] = [DatasetRawDTO(**version) for version in data["versions"]]
        data["id"] = uuid.UUID(data["id"])
        dataset = Dataset.from_dict(data)
        return dataset

    def get_checksum_by_buid(self, dataset_buid) -> str or None:
        data = self.client.fetchone(
            """SELECT dv.checksum FROM dataset_versions dv JOIN datasets d ON d.id = dv.dataset_id WHERE d.buid = %s ORDER BY dv.timestamp DESC LIMIT 1""",
            (str(dataset_buid),),
        )
        if data is not None:
            return data.get("checksum", None)
        return
