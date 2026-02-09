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
