from __future__ import annotations

from typing import Optional
from uuid import UUID

from domain.common.value_objects import Slug, Url


class Platform:
    def __init__(
        self,
        id: UUID,
        name: str,
        slug: str | Slug,
        type: str,
        url: str | Url,
        organization_id: str,
        key: Optional[str],
        datasets_count=0,
        last_sync=None,
        created_at=None,
        last_sync_status="pending",
    ):
        self.id = id
        self.name = name
        self.slug = slug if isinstance(slug, Slug) else Slug(slug)
        self.organization_id = organization_id
        self.type = type
        self.url = url if isinstance(url, Url) else Url(url)
        self.key = key
        self.datasets_count = datasets_count
        self.last_sync = last_sync
        self.last_sync_status = last_sync_status
        self.created_at = created_at
        self.syncs = []

    def sync(self, timestamp, status, datasets_count):
        self.datasets_count = datasets_count
        self.last_sync = timestamp
        self.last_sync_status = status
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
