from __future__ import annotations

from uuid import UUID

from domain.common.enums import PlatformType, SyncStatus
from domain.common.value_objects import Slug, Url


class Platform:
    def __init__(
        self,
        id: UUID,
        name: str,
        slug: str | Slug,
        type: str | PlatformType,
        url: str | Url,
        organization_id: str,
        key: str | None,
        datasets_count=0,
        last_sync=None,
        created_at=None,
        last_sync_status: str | SyncStatus = SyncStatus.PENDING,
    ):
        self.id = id
        self.name = name
        self.slug = slug if isinstance(slug, Slug) else Slug(slug)
        self.organization_id = organization_id
        # Accept PlatformType enum or any string (for flexibility in tests)
        self.type = type if isinstance(type, (PlatformType, str)) else str(type)
        self.url = url if isinstance(url, Url) else Url(url)
        self.key = key
        self.datasets_count = datasets_count
        self.last_sync = last_sync
        self.last_sync_status = (
            last_sync_status if isinstance(last_sync_status, SyncStatus) else SyncStatus(last_sync_status)
        )
        self.created_at = created_at
        self.syncs = []

    def sync(self, timestamp, status: str | SyncStatus, datasets_count):
        self.datasets_count = datasets_count
        self.last_sync = timestamp
        self.last_sync_status = status if isinstance(status, SyncStatus) else SyncStatus(status)
        return {
            "platform_id": self.id,
            "timestamp": timestamp,
            "status": status,
            "datasets_count": datasets_count,
        }

    def add_sync(self, sync):
        self.syncs.append(sync)

    def __str__(self):
        return f"<Platform: {self.name}>"
