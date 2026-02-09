import uuid

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository
from infrastructure.database.postgres import PostgresClient


class PostgresPlatformRepository(PlatformRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def save(self, platform: Platform) -> None:
        self.client.execute(
            """INSERT INTO platforms (
                id, name, slug, type, url, organization_id, key, datasets_count, last_sync, last_sync_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                str(platform.id),
                platform.name,
                str(platform.slug),
                platform.type,
                str(platform.url),
                platform.organization_id,
                platform.key,
                platform.datasets_count,
                platform.last_sync,
                platform.last_sync_status,
            ),
        )

    def get(self, platform_id: uuid.UUID) -> Platform | None:
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

        if row is None:
            raise ValueError(f"Platform not found for domain: {domain}")

        row["id"] = uuid.UUID(row["id"])
        return Platform(**{k: v for k, v in row.items()})

    def save_sync(self, platform_id, payload):
        self.client.execute(
            """UPDATE platforms SET datasets_count = %s, last_sync = %s , last_sync_status = %s WHERE id = %s;""",
            (
                payload["datasets_count"],
                payload["timestamp"],
                payload["status"],
                str(platform_id),
            ),
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
        return self.client.fetchall("""
        SELECT
    p.*,
    json_agg(
        json_build_object(
            'id', h.id,
            'platform_id', h.platform_id,
            'timestamp', h.timestamp,
            'status', h.status,
            'datasets_count', h.datasets_count
        ) ORDER BY h.timestamp DESC
    ) FILTER (WHERE h.platform_id IS NOT NULL) AS syncs
FROM platforms p
LEFT JOIN platform_sync_histories h ON p.id = h.platform_id
GROUP BY p.id, p.created_at
ORDER BY p.created_at DESC;
        """)
