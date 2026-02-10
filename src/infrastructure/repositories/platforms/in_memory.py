from uuid import UUID

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository


class InMemoryPlatformRepository(PlatformRepository):
    def __init__(self, db):
        self.db = db
        self.syncs = []

    def save(self, data):
        self.db.append(data)

    def get(self, platform_id: UUID) -> Platform | None:
        """Retrieve a platform aggregate by ID, including its sync history."""
        platform = next((item for item in self.db if item.id == platform_id), None)
        if platform:
            # Reconstruct sync history for this aggregate
            syncs = [item for item in self.syncs if item["platform_id"] == platform_id]
            for sync in syncs:
                platform.add_sync(sync)
        return platform

    def get_by_domain(self, domain: str) -> Platform | None:
        """Find a platform by its domain string."""
        return next((item for item in self.db if domain in str(item.url)), None)

    def all(self) -> list[Platform]:
        """Return all registered platform aggregates."""
        return self.db

    def save_sync(self, platform_id, payload):
        self.syncs.append({"platform_id": platform_id, **payload})
