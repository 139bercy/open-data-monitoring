from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from common import JsonSerializer
from domain.common.enums import SyncStatus
from domain.common.value_objects import Slug, Url
from domain.datasets.entities import DatasetVersion
from domain.datasets.exceptions import (
    DatasetAlreadyDeletedError,
    DatasetNotDeletedError,
    InvalidMetricValueError,
)
from domain.datasets.value_objects import DatasetQuality


class Dataset:
    def __init__(
        self,
        id: UUID,
        platform_id: UUID,
        buid: str,
        slug: str | Slug,
        title: str,
        page: str | Url,
        created: datetime,
        modified: datetime,
        published: bool,
        restricted: bool,
        downloads_count: int,
        api_calls_count: int,
        raw: dict,
        publisher: str | None = None,
        last_sync_status: str | SyncStatus | None = None,
        is_deleted: bool = False,
        views_count: int | None = None,
        reuses_count: int | None = None,
        followers_count: int | None = None,
        popularity_score: float | None = None,
        last_version_timestamp: datetime | None = None,
        checksum: str | None = None,
    ):
        self.id = id
        self.platform_id = platform_id
        self.buid = buid
        self.slug = slug if isinstance(slug, Slug) else Slug(slug)
        self.title = title
        self.page = page if isinstance(page, Url) else Url(page)
        self.publisher = publisher
        self.created = created
        self.modified = modified
        self.published = published
        self.restricted = restricted
        self.downloads_count = downloads_count
        self.api_calls_count = api_calls_count
        self.views_count = views_count
        self.reuses_count = reuses_count
        self.followers_count = followers_count
        self.popularity_score = popularity_score
        self.raw = raw
        self.checksum = checksum
        self.versions: list[DatasetVersion] | None = []
        self.last_sync_status = (
            last_sync_status
            if last_sync_status is None or isinstance(last_sync_status, SyncStatus)
            else SyncStatus(last_sync_status)
        )
        self.last_version_timestamp = last_version_timestamp
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
            "title": self.title,
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
        downloads_count: int | None = None,
        api_calls_count: int | None = None,
        views_count: int | None = None,
        reuses_count: int | None = None,
        followers_count: int | None = None,
        popularity_score: float | None = None,
        diff: dict | None = None,
        metadata_volatile: dict | None = None,
        **kwargs,
    ):
        version = DatasetVersion(
            dataset_id=dataset_id,
            snapshot=snapshot,
            checksum=checksum,
            downloads_count=downloads_count,
            api_calls_count=api_calls_count,
            views_count=views_count,
            reuses_count=reuses_count,
            followers_count=followers_count,
            popularity_score=popularity_score,
            diff=diff,
            metadata_volatile=metadata_volatile,
        )
        self.versions.append(version)

    def add_quality(
        self, downloads_count, api_calls_count, has_description, is_slug_valid=True, evaluation_results=None
    ):
        self.quality = DatasetQuality(
            downloads_count=downloads_count,
            api_calls_count=api_calls_count,
            has_description=has_description,
            is_slug_valid=is_slug_valid,
            evaluation_results=evaluation_results,
        )

    def mark_as_deleted(self) -> None:
        """Mark this dataset as deleted from the platform."""
        if self.is_deleted:
            raise DatasetAlreadyDeletedError(f"Dataset {self.id} is already marked as deleted")
        self.is_deleted = True

    def restore(self) -> None:
        """Restore a previously deleted dataset."""
        if not self.is_deleted:
            raise DatasetNotDeletedError(f"Dataset {self.id} is not deleted")
        self.is_deleted = False

    def update_metrics(
        self,
        downloads: int | None = None,
        api_calls: int | None = None,
        views: int | None = None,
        reuses: int | None = None,
        followers: int | None = None,
        popularity: float | None = None,
    ) -> None:
        """Update dataset metrics with validation."""
        metrics = {
            "downloads_count": downloads,
            "api_calls_count": api_calls,
            "views_count": views,
            "reuses_count": reuses,
            "followers_count": followers,
            "popularity_score": popularity,
        }

        for attr_name, value in metrics.items():
            if value is not None:
                if value < 0:
                    raise InvalidMetricValueError(attr_name, value)
                setattr(self, attr_name, value)

    def prepare_for_persistence(self) -> None:
        """Prepare aggregate for persistence (calculate hash, ensure active)."""
        self.calculate_hash()
        # Force reactivation if dataset is found by crawler
        if self.is_deleted:
            self.restore()

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=UUID(data["id"]) if not isinstance(data["id"], UUID) else data["id"],
            platform_id=(
                UUID(data["platform_id"]) if not isinstance(data["platform_id"], UUID) else data["platform_id"]
            ),
            buid=data["buid"],
            slug=data["slug"],
            title=data.get("title", data.get("slug")),  # Fallback to slug if title missing
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
            views_count=data.get("views_count"),
            reuses_count=data.get("reuses_count"),
            followers_count=data.get("followers_count"),
            popularity_score=data.get("popularity_score"),
            last_sync_status=data.get("last_sync_status"),
            last_version_timestamp=data.get("last_version_timestamp"),
            checksum=data.get("checksum"),
            is_deleted=data.get("deleted", data.get("is_deleted", False)),
        )

    def __repr__(self):
        return f"<Dataset: {self.slug}>"

    def __str__(self):
        versions, quality = [asdict(version) for version in self.versions], asdict(self.quality)
        self.versions, self.quality = versions, quality
        return json.dumps(self.__dict__, indent=2, cls=JsonSerializer)
