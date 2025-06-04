import uuid
from typing import Optional

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository
from infrastructure.database.client import PostgresClient


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
        self.client.commit()

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

        # Conversion UUID si besoin
        row['id'] = uuid.UUID(row['id'])
        platform = Platform(**{k: v for k, v in row.items() if k != 'syncs'})

        # Ajout des synchronisations
        if row['syncs']:
            for sync in row['syncs']:
                platform.add_sync(sync)

        return platform

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
        self.client.commit()

    def all(self):
        pass
