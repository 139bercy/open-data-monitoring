import uuid

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

    def get(self, platform_id: uuid.UUID) -> Platform:
        row = self.client.fetchone(
            "SELECT * FROM platforms WHERE id = %s", (str(platform_id),)
        )
        if not row:
            return None
        row["id"] = (
            uuid.UUID(row["id"]) if not isinstance(row["id"], uuid.UUID) else row["id"]
        )
        return Platform(**row)

    def all(self):
        pass
