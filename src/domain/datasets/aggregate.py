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
from domain.datasets.services.syntax_analyzer import SyntaxAnalyzer
from domain.datasets.value_objects import DatasetQuality, DiscoverabilityKPI, ImpactKPI


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
        linked_dataset_id: UUID | None = None,
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
        self.linked_dataset_id = linked_dataset_id

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
        self,
        downloads_count,
        api_calls_count,
        has_description,
        is_slug_valid=True,
        evaluation_results=None,
        previous_raw=None,
        **kwargs,
    ):
        syntax_score = None
        if previous_raw:
            analysis = SyntaxAnalyzer.analyze_change(previous_raw, self.raw)
            syntax_score = analysis.get("syntax_score")

        self.quality = DatasetQuality(
            downloads_count=downloads_count,
            api_calls_count=api_calls_count,
            has_description=has_description,
            is_slug_valid=is_slug_valid,
            evaluation_results=evaluation_results,
            discoverability=self.calculate_discoverability_kpi(evaluation_results),
            impact=self.calculate_impact_kpi(),
            syntax_change_score=syntax_score,
        )

    def calculate_discoverability_kpi(self, evaluation_results: dict | None = None) -> DiscoverabilityKPI:  # noqa: C901
        """
        Calculates the discoverability KPI based on metadata and charter rules.
        """
        # 1. SEO Score (Title 5-10 words)
        words = self.title.split() if self.title else []
        word_count = len(words)
        if 5 <= word_count <= 10:
            seo_score = 100.0
        else:
            # Degressive score: 100% at boundaries, dropping to 0% at +/- 5 words
            distance = min(abs(word_count - 5), abs(word_count - 10))
            seo_score = max(0.0, 100.0 - (distance * 20.0))

        # 2. DCAT Completeness
        # We look into evaluation_results if present, or basic presence
        dcat_score = 0.0
        if evaluation_results and "criteria_scores" in evaluation_results:
            dcat_criteria = [
                s for s in evaluation_results["criteria_scores"].values() if s.get("category") == "administrative"
            ]
            if dcat_criteria:
                dcat_score = sum(s.get("score", 0) for s in dcat_criteria) / len(dcat_criteria)
        else:
            # Fallback algorithmic check
            mandatory_fields = ["publisher", "created", "modified", "page"]
            present = sum(1 for field in mandatory_fields if getattr(self, field, None))
            if self.has_description():
                present += 1
                mandatory_fields.append("description")
            dcat_score = (present / len(mandatory_fields)) * 100.0

        # 3. Freshness (Relative to expected frequency)
        # Ensure modified is a datetime object (can be str if from some DTOs)
        modified_dt = self.modified
        if isinstance(modified_dt, str):
            modified_dt = datetime.fromisoformat(modified_dt.replace("Z", "+00:00"))

        if modified_dt.tzinfo is None:
            modified_dt = modified_dt.replace(tzinfo=timezone.utc)

        frequency = self.raw.get("frequency")
        if not frequency:
            # Safe traversal addressing ODS null metas anomaly
            metas = self.raw.get("metas") or {}
            default_meta = metas.get("default") or {} if metas else {}
            frequency = default_meta.get("accrual_periodicity")

        # Mapping to days (including grace period)
        frequency_thresholds = {
            "daily": 2,
            "continuous": 2,
            "weekly": 9,
            "monthly": 37,
            "quarterly": 105,
            "semiannual": 210,
            "annual": 395,
            "punctual": 3650,  # 10 years for punctual
        }

        default_threshold = 90  # Penalty for unknown frequency
        threshold_days = frequency_thresholds.get(str(frequency).lower(), default_threshold)

        delta_days = (datetime.now(timezone.utc) - modified_dt).days
        if delta_days <= threshold_days:
            freshness_score = 100.0
        elif delta_days <= threshold_days * 2:
            freshness_score = 50.0
        else:
            freshness_score = 0.0

        # 4. Semantic Quality (from IA if available)
        semantic_score = None
        if evaluation_results and "criteria_scores" in evaluation_results:
            desc_criteria = [
                s for s in evaluation_results["criteria_scores"].values() if s.get("category") == "descriptive"
            ]
            if desc_criteria:
                semantic_score = sum(s.get("score", 0) for s in desc_criteria) / len(desc_criteria)

        return DiscoverabilityKPI(
            seo_score=seo_score,
            dcat_completeness_score=dcat_score,
            freshness_score=freshness_score,
            semantic_quality_score=semantic_score,
        )

    def calculate_impact_kpi(self) -> ImpactKPI:
        """
        Calculates the impact KPI based on usage metrics.
        """
        # 1. Engagement Rate (reuses / views)
        engagement = 0.0
        if self.views_count and self.views_count > 0:
            engagement = (self.reuses_count or 0) / self.views_count

        # 2. Usage Intensity (API calls vs Downloads)
        intensity = 0.0
        total_usage = (self.api_calls_count or 0) + (self.downloads_count or 0)
        if total_usage > 0:
            intensity = (self.api_calls_count or 0) / total_usage

        # 3. Popularity score (already normalized by platform usually)
        popularity = self.popularity_score or 0.0

        return ImpactKPI(engagement_rate=engagement, usage_intensity=intensity, popularity_score=popularity)

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

    def extract_external_link_slug(self) -> str | None:
        """
        Attempts to find a reference to another dataset in the metadata.
        Returns the first valid slug found from either ODS or DataGouv-style metadata.
        """
        return self._extract_slug_from_ods() or self._extract_slug_from_datagouv()

    def _extract_slug_from_ods(self) -> str | None:
        """Extracts DataGouv slug from ODS 'source' metadata fields."""
        paths = [
            ["metadata", "default", "source"],
            ["metas", "default", "source"],
            ["metadata", "default", "source", "value"],
        ]

        for path in paths:
            val = self._get_raw_value(path)
            if val and "data.gouv.fr" in val and "/datasets/" in val:
                parts = val.split("/datasets/")
                if len(parts) > 1:
                    return parts[1].split("/")[0]
        return None

    def _extract_slug_from_datagouv(self) -> str | None:
        """Extracts ODS slug from DataGouv 'harvest' metadata fields or description."""
        # 1. Check harvest harvest fields
        paths = [
            ["harvest", "remote_url"],
            ["harvest", "uri"],
            ["harvest", "remote_id"],
        ]

        for path in paths:
            val = self._get_raw_value(path)
            if val and "/explore/dataset/" in val:
                parts = val.split("/explore/dataset/")
                if len(parts) > 1:
                    return parts[1].strip("/").split("/")[0]

        # 2. Fallback: Check description for ODS explore URLs
        description = self.raw.get("description")
        if description and "data.economie.gouv.fr/explore/dataset/" in description:
            parts = description.split("data.economie.gouv.fr/explore/dataset/")
            if len(parts) > 1:
                # Basic cleaning of the extracted slug
                return parts[1].split("/")[0].split(")")[0].split('"')[0].strip()

        return None

    def _get_raw_value(self, path: list[str]) -> str | None:
        """Helper to safely traverse the raw metadata dictionary."""
        current = self.raw
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key, {})
        return current if isinstance(current, str) else None

    def has_description(self) -> bool:
        """Determine if description is missing (handling nested structures for ODS/DataGouv)."""

        def get_nested(d, *keys):
            for k in keys:
                if not isinstance(d, dict):
                    return None
                d = d.get(k)
            return d

        raw_dataset = self.raw
        if raw_dataset.get("description"):
            return True
        if get_nested(raw_dataset, "metas", "default", "description"):
            return True
        if get_nested(raw_dataset, "metadata", "default", "description"):
            return True
        if get_nested(raw_dataset, "metadata", "default", "description", "value"):
            # Handle ODS V2 value-wrapped strings if present
            return True
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
            linked_dataset_id=(
                UUID(data["linked_dataset_id"])
                if data.get("linked_dataset_id") and not isinstance(data["linked_dataset_id"], UUID)
                else data.get("linked_dataset_id")
            ),
        )

    def to_dict(self) -> dict:
        """Convert aggregate state to a serializable dictionary."""
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        data["slug"] = str(self.slug)
        data["page"] = str(self.page)
        data["last_sync_status"] = self.last_sync_status.value if self.last_sync_status else None
        data["quality"] = asdict(self.quality) if self.quality else None
        data["versions"] = [asdict(v) for v in self.versions] if self.versions else []
        data["linked_dataset_id"] = str(self.linked_dataset_id) if self.linked_dataset_id else None
        return data

    def __repr__(self) -> str:
        return f"<Dataset: {self.slug}>"

    def __str__(self) -> str:
        """Non-destructive string representation."""
        return json.dumps(self.to_dict(), indent=2, cls=JsonSerializer)
