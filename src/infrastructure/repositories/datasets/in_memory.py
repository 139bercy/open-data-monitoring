import uuid
from collections import Counter
from datetime import datetime, timezone

from common import calculate_snapshot_diff
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import AbstractDatasetRepository
from domain.datasets.value_objects import DatasetVersionParams


class InMemoryDatasetRepository(AbstractDatasetRepository):
    def __init__(self, db):
        self.db = db
        self.versions = []

    def add(self, dataset: Dataset):
        for i, existing in enumerate(self.db):
            if existing.id == dataset.id:
                self.db[i] = dataset
                return
        self.db.append(dataset)

    def add_version(self, params: "DatasetVersionParams") -> None:
        """Add a new version of a dataset using Parameter Object pattern."""
        diff = params.diff  # Start with provided diff

        if not diff:
            prev_version_dict = next((v for v in reversed(self.versions) if v["dataset_id"] == params.dataset_id), None)
            if prev_version_dict:
                # Construct comparable objects including metrics
                prev_comparable = prev_version_dict["snapshot"].copy() if prev_version_dict["snapshot"] else {}
                prev_comparable.update(
                    {
                        "downloads_count": prev_version_dict.get("downloads_count"),
                        "api_calls_count": prev_version_dict.get("api_calls_count"),
                        "views_count": prev_version_dict.get("views_count"),
                        "reuses_count": prev_version_dict.get("reuses_count") or 0,
                        "followers_count": prev_version_dict.get("followers_count"),
                        "popularity_score": prev_version_dict.get("popularity_score"),
                    }
                )

                curr_comparable = params.snapshot.copy()
                curr_comparable.update(
                    {
                        "downloads_count": params.downloads_count,
                        "api_calls_count": params.api_calls_count,
                        "views_count": params.views_count,
                        "reuses_count": params.reuses_count or 0,
                        "followers_count": params.followers_count,
                        "popularity_score": params.popularity_score,
                    }
                )
                diff = calculate_snapshot_diff(prev_comparable, curr_comparable)

        self.versions.append(
            {
                "dataset_id": params.dataset_id,
                "timestamp": datetime.now(timezone.utc),
                "snapshot": params.snapshot,
                "checksum": params.checksum,
                "title": params.title,
                "downloads_count": params.downloads_count,
                "api_calls_count": params.api_calls_count,
                "views_count": params.views_count,
                "reuses_count": params.reuses_count,
                "followers_count": params.followers_count,
                "popularity_score": params.popularity_score,
                "diff": diff,
                "metadata_volatile": None,  # Not used in Parameter Object
            }
        )

    def get(self, dataset_id) -> Dataset:
        dataset = next((item for item in self.db if item.id == dataset_id), None)
        if dataset is not None:
            dataset.versions = [item for item in self.versions if item["dataset_id"] == dataset_id]
            if dataset.versions:
                dataset.last_version_timestamp = dataset.versions[-1].get("timestamp")
                dataset.checksum = dataset.versions[-1].get("checksum")
            return dataset
        return

    def get_checksum_by_buid(self, dataset_buid) -> str | None:
        dataset = next((item for item in self.db if item.buid == dataset_buid), None)
        if dataset is not None:
            versions = [item for item in self.versions if item["dataset_id"] == dataset.id]
            if versions:
                return versions[-1].get("checksum")
            return dataset.checksum
        return

    def get_by_buid(self, dataset_buid: str) -> Dataset | None:
        dataset = next((item for item in self.db if item.buid == dataset_buid), None)
        if dataset is not None:
            versions = [item for item in self.versions if item["dataset_id"] == dataset.id]
            if versions:
                dataset.last_version_timestamp = versions[-1].get("timestamp")
                dataset.checksum = versions[-1].get("checksum")
            return dataset
        return

    def get_publishers_stats(self) -> list[dict[str, any]]:
        """Récupère les statistiques des publishers (nom et nombre de datasets) - Version in-memory"""
        publishers = [dataset.publisher for dataset in self.db if dataset.publisher]
        publisher_counts = Counter(publishers)

        return [
            {"publisher": publisher, "dataset_count": count} for publisher, count in sorted(publisher_counts.items())
        ]

    def get_id_by_slug(self, platform_id, slug):
        dataset = next((item for item in self.db if str(item.slug) == str(slug)), None)
        if dataset is not None:
            return dataset.id
        return

    def update_dataset_sync_status(self, platform_id, dataset_id, status):
        instance = self.get(dataset_id=dataset_id)
        instance.last_sync_status = status
        self.add(instance)
        return

    def get_buids(self, platform_id):
        return [dataset.buid for dataset in self.db if dataset.platform_id == platform_id]

    def update_dataset_state(self, dataset: Dataset) -> None:
        instance = self.get(dataset_id=dataset.id)
        instance.is_deleted = dataset.is_deleted
        self.add(instance)

    def search(
        self,
        platform_id: str | None = None,
        publisher: str | None = None,
        q: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        modified_from: str | None = None,
        modified_to: str | None = None,
        is_deleted: bool | None = None,
        sort_by: str = "modified",
        order: str = "desc",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[dict], int]:
        """Basic in-memory search implementation for tests."""
        results = [d for d in self.db]

        # Simple filtering
        if platform_id:
            results = [d for d in results if str(d.platform_id) == str(platform_id)]
        if publisher:
            results = [d for d in results if d.publisher == publisher]
        if q:
            results = [d for d in results if q.lower() in str(d.slug).lower()]
        if is_deleted is not None:
            results = [d for d in results if d.is_deleted == is_deleted]

        # Sort (very basic)
        reverse = order.lower() == "desc"
        if sort_by == "created":
            results.sort(key=lambda d: d.created or datetime.min, reverse=reverse)
        elif sort_by == "modified":
            results.sort(key=lambda d: d.modified or datetime.min, reverse=reverse)

        total = len(results)
        offset = (page - 1) * page_size
        paginated = results[offset : offset + page_size]

        # Map to dict (simplified version of Postgres search output)
        items = []
        for d in paginated:
            items.append(
                {
                    "id": d.id,
                    "platform_id": d.platform_id,
                    "publisher": d.publisher,
                    "title": d.title or str(d.slug),
                    "timestamp": None,
                    "created": d.created.isoformat() if d.created else None,
                    "modified": d.modified.isoformat() if d.modified else None,
                    "restricted": d.restricted,
                    "published": d.published,
                    "downloads_count": getattr(d, "downloads_count", 0),
                    "api_calls_count": getattr(d, "api_calls_count", 0),
                    "views_count": getattr(d, "views_count", 0),
                    "reuses_count": getattr(d, "reuses_count", 0),
                    "followers_count": getattr(d, "followers_count", 0),
                    "popularity_score": getattr(d, "popularity_score", 0),
                    "versions_count": len([v for v in self.versions if v["dataset_id"] == d.id]),
                    "page": d.page,
                    "last_sync": d.last_sync,
                    "last_sync_status": d.last_sync_status,
                    "deleted": d.is_deleted,
                    "quality": {
                        "has_description": (
                            getattr(d.quality, "has_description", None) if hasattr(d, "quality") else None
                        ),
                        "is_slug_valid": getattr(d.quality, "is_slug_valid", True) if hasattr(d, "quality") else True,
                        "evaluation_results": (
                            getattr(d.quality, "evaluation_results", None) if hasattr(d, "quality") else None
                        ),
                    },
                }
            )

        return items, total

    def get_detail(self, dataset_id: uuid.UUID, include_snapshots: bool = False) -> dict | None:
        """Get full dataset details (In-memory implementation)."""
        dataset = self.get(dataset_id)
        if not dataset:
            return None

        # Current snapshot
        current_snapshot = None
        if dataset.versions:
            r = dataset.versions[-1]
            current_snapshot = {
                "id": uuid.UUID(str(uuid.uuid4())),  # Mock ID for in-memory
                "timestamp": r["timestamp"],
                "downloads_count": r.get("downloads_count"),
                "api_calls_count": r.get("api_calls_count"),
                "views_count": r.get("views_count"),
                "reuses_count": r.get("reuses_count"),
                "followers_count": r.get("followers_count"),
                "popularity_score": r.get("popularity_score"),
                "title": r.get("title"),
                "data": r.get("snapshot"),
            }

        # Optional snapshots list
        snapshots = None
        if include_snapshots:
            snapshots = [
                {
                    "id": uuid.UUID(str(uuid.uuid4())),
                    "timestamp": r["timestamp"],
                    "downloads_count": r.get("downloads_count"),
                    "api_calls_count": r.get("api_calls_count"),
                    "views_count": r.get("views_count"),
                    "reuses_count": r.get("reuses_count"),
                    "followers_count": r.get("followers_count"),
                    "popularity_score": r.get("popularity_score"),
                    "title": r.get("title"),
                    "data": r.get("snapshot"),
                }
                for r in reversed(dataset.versions)
            ][:50]

        return {
            "id": dataset.id,
            "platform_id": dataset.platform_id,
            "publisher": dataset.publisher,
            "title": current_snapshot.get("title") if current_snapshot else str(dataset.slug),
            "buid": dataset.buid,
            "slug": str(dataset.slug),
            "page": str(dataset.page),
            "created": dataset.created,
            "modified": dataset.modified,
            "published": dataset.published,
            "restricted": dataset.restricted,
            "deleted": dataset.is_deleted,
            "last_sync": dataset.last_sync,
            "last_sync_status": dataset.last_sync_status,
            "quality": {
                "has_description": (
                    getattr(dataset.quality, "has_description", None) if hasattr(dataset, "quality") else None
                ),
                "is_slug_valid": (
                    getattr(dataset.quality, "is_slug_valid", True) if hasattr(dataset, "quality") else True
                ),
                "evaluation_results": (
                    getattr(dataset.quality, "evaluation_results", None) if hasattr(dataset, "quality") else None
                ),
            },
            "current_snapshot": current_snapshot,
            "snapshots": snapshots,
        }

    def get_versions(self, dataset_id: uuid.UUID, page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
        """Get paginated version history for a dataset (In-memory implementation)."""
        dataset_versions = [v for v in self.versions if v["dataset_id"] == dataset_id]
        dataset_versions.sort(key=lambda v: v["timestamp"], reverse=True)

        total = len(dataset_versions)
        offset = (max(1, page) - 1) * page_size
        paginated = dataset_versions[offset : offset + page_size]

        items = [
            {
                "id": uuid.UUID(str(uuid.uuid4())),
                "timestamp": v["timestamp"],
                "downloads_count": v.get("downloads_count"),
                "api_calls_count": v.get("api_calls_count"),
                "views_count": v.get("views_count"),
                "reuses_count": v.get("reuses_count"),
                "followers_count": v.get("followers_count"),
                "popularity_score": v.get("popularity_score"),
                "title": v.get("title"),
                "diff": v.get("diff"),
                "data": v.get("snapshot"),
            }
            for v in paginated
        ]

        return items, total
