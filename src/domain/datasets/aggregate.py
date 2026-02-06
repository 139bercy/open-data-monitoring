from __future__ import annotations
import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from common import JsonSerializer
from domain.common.value_objects import Slug, Url
from domain.datasets.entities import DatasetVersion
from domain.datasets.value_objects import DatasetQuality


class Dataset:
    def __init__(
        self,
        id: UUID,
        platform_id: UUID,
        buid: str,
        slug: str | Slug,
        page: str | Url,
        created: datetime,
        modified: datetime,
        published: bool,
        restricted: bool,
        downloads_count: int,
        api_calls_count: int,
        raw: dict,
        publisher: Optional[str] = None,
        last_sync_status: str = None,
        is_deleted: bool = False,
    ):
        self.id = id
        self.platform_id = platform_id
        self.buid = buid
        self.slug = slug if isinstance(slug, Slug) else Slug(slug)
        self.page = page if isinstance(page, Url) else Url(page)
        self.publisher = publisher
        self.created = created
        self.modified = modified
        self.published = published
        self.restricted = restricted
        self.downloads_count = downloads_count
        self.api_calls_count = api_calls_count
        self.raw = raw
        self.checksum = None
        self.versions: List[DatasetVersion] | None = []
        self.last_sync_status = last_sync_status
        self.quality = None
        self.is_deleted = is_deleted

    def is_modified_since(self, date: datetime) -> bool:
        return self.modified > date

    def calculate_hash(self) -> str:
        """
        Calculates a stable hash based ONLY on domain fields.
        This ensures the hash is independent of the external raw dictionary structure.
        """
        # We only use core identifying and versioned data fields
        state = {
            "buid": self.buid,
            "slug": str(self.slug),
            "page": str(self.page),
            "created": self.created.isoformat() if isinstance(self.created, datetime) else self.created,
            "modified": self.modified.isoformat() if isinstance(self.modified, datetime) else self.modified,
            "published": self.published,
            "restricted": self.restricted,
            "publisher": self.publisher,
        }
        
        state_str = json.dumps(state, sort_keys=True)
        self.checksum = hashlib.sha256(state_str.encode()).hexdigest()
        return self.checksum

    def add_version(
        self,
        dataset_id: str,
        snapshot: dict,
        checksum: str,
        downloads_count: int,
        api_calls_count: int,
    ):
        version = DatasetVersion(
            dataset_id=dataset_id,
            snapshot=snapshot,
            checksum=checksum,
            downloads_count=downloads_count,
            api_calls_count=api_calls_count,
        )
        self.versions.append(version)

    def add_quality(self, downloads_count, api_calls_count, has_description):
        self.quality = DatasetQuality(
            downloads_count=downloads_count,
            api_calls_count=api_calls_count,
            has_description=has_description,
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=UUID(data["id"]) if not isinstance(data["id"], UUID) else data["id"],
            platform_id=(
                UUID(data["platform_id"]) if not isinstance(data["platform_id"], UUID) else data["platform_id"]
            ),
            buid=data["buid"],
            slug=data["slug"],
            page=data["page"],
            created=(
                data["created"] if isinstance(data["created"], datetime) else datetime.fromisoformat(data["created"])
            ),
            modified=(
                data["modified"] if isinstance(data["modified"], datetime) else datetime.fromisoformat(data["modified"])
            ),
            published=bool(data.get("published", True)),
            restricted=bool(data.get("restricted", False)),
            raw=data.get("raw", {}),
            publisher=data.get("publisher"),
            downloads_count=data.get("downloads_count"),
            api_calls_count=data.get("api_calls_count"),
            last_sync_status=data.get("last_sync_status"),
            is_deleted=data.get("deleted", data.get("is_deleted", False)),
        )

    def __repr__(self):
        return f"<Dataset: {self.slug}>"

    def __str__(self):
        versions, quality = [asdict(version) for version in self.versions], asdict(self.quality)
        self.versions, self.quality = versions, quality
        return json.dumps(self.__dict__, indent=2, cls=JsonSerializer)
