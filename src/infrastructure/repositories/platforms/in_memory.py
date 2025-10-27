from uuid import UUID

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository


class InMemoryPlatformRepository(PlatformRepository):
    def __init__(self, db):
        self.db = db
        self.syncs = []

    def save(self, data):
        self.db.append(data)

    def get(self, platform_id: UUID) -> Platform:
        syncs = [item for item in self.syncs if item["platform_id"] == platform_id]
        platform = next((item for item in self.db if item.id == platform_id), None)
        if len(syncs) is not None:
            for sync in syncs:
                if platform is not None:
                    platform.add_sync(sync)

        if platform is None:
            raise ValueError(f"Platform with id {platform_id} not found")

        return platform

    def get_by_domain(self, domain) -> Platform:
        platform = next((item for item in self.db if domain in item.url), None)
        if platform is not None:
            return platform
        raise ValueError(f"Platform with domain {domain} not found")

    def all(self):
        return self.db

    def save_sync(self, platform_id, payload):
        self.syncs.append({"platform_id": platform_id, **payload})
