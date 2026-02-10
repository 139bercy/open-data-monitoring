from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from common import JsonSerializer
from domain.common.constants import DEFAULT_VERSIONING_COOLDOWN_HOURS
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
        if self.is_deleted:
            self.restore()

    def merge_with_existing(self, other: Dataset) -> None:
        """Merge this instance with existing dataset, preserving ID."""
        self.id = other.id

    def has_metrics_changed(self, other: Dataset) -> bool:
        """Check if metrics have changed between versions."""
        return (
            self.downloads_count != other.downloads_count
            or self.api_calls_count != other.api_calls_count
            or (
                self.views_count != other.views_count
                if self.views_count is not None or other.views_count is not None
                else False
            )
            or (
                self.reuses_count != other.reuses_count
                if self.reuses_count is not None or other.reuses_count is not None
                else False
            )
            or (
                self.followers_count != other.followers_count
                if self.followers_count is not None or other.followers_count is not None
                else False
            )
            or (
                self.popularity_score != other.popularity_score
                if self.popularity_score is not None or other.popularity_score is not None
                else False
            )
        )

    def is_cooldown_active(self, hours: int = DEFAULT_VERSIONING_COOLDOWN_HOURS) -> bool:
        """Check if cooldown period is active for metric-only changes."""
        if not self.last_version_timestamp:
            return False

        now = datetime.now(timezone.utc)
        last_ts = self.last_version_timestamp
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)

        return (now - last_ts) < timedelta(hours=hours)

    def should_version(self, new_instance: Dataset) -> bool:
        """Determine if a new version should be created based on changes."""
        if self.checksum != new_instance.checksum:
            return True
        if self.is_deleted != new_instance.is_deleted:
            return True

        if self.has_metrics_changed(new_instance):
            return not self.is_cooldown_active()

        return False

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

    def to_dict(self) -> dict:
        """Convert aggregate state to a serializable dictionary."""
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        data["slug"] = str(self.slug)
        data["page"] = str(self.page)
        data["last_sync_status"] = self.last_sync_status.value if self.last_sync_status else None
        data["quality"] = asdict(self.quality) if self.quality else None
        data["versions"] = [asdict(v) for v in self.versions] if self.versions else []
        return data

    def __repr__(self) -> str:
        return f"<Dataset: {self.slug}>"

    def __str__(self) -> str:
        """Non-destructive string representation."""
        return json.dumps(self.to_dict(), indent=2, cls=JsonSerializer)
