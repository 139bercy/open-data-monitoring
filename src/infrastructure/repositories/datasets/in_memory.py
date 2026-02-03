from typing import Optional
from uuid import UUID

from domain.datasets.aggregate import Dataset
from domain.datasets.ports import AbstractDatasetRepository


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

    def add_version(
        self,
        dataset_id: UUID,
        snapshot: dict,
        checksum: str,
        downloads_count: int,
        api_calls_count: int,
    ) -> None:
        self.versions.append(
            {
                "dataset_id": dataset_id,
                "snapshot": snapshot,
                "checksum": checksum,
                "downloads_count": downloads_count,
                "api_calls_count": api_calls_count,
            }
        )

    def get(self, dataset_id) -> Dataset:
        dataset = next((item for item in self.db if item.id == dataset_id), None)
        if dataset is not None:
            dataset.versions = [item for item in self.versions if item["dataset_id"] == dataset_id]
        if dataset is None:
            raise ValueError(f"Dataset with id {dataset_id} not found")
        return dataset

    def get_checksum_by_buid(self, dataset_buid) -> Optional[str]:
        dataset = next((item for item in self.db if item.buid == dataset_buid), None)
        if dataset is not None:
            return dataset.checksum
        return

    def get_by_buid(self, dataset_buid: str) -> Optional[Dataset]:
        dataset = next((item for item in self.db if item.buid == dataset_buid), None)
        if dataset is not None:
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
        dataset = next((item for item in self.db if item.slug == slug), None)
        if dataset is not None:
            return dataset.id
        return

    def update_dataset_sync_status(self, platform_id, dataset_id, status):
        instance = self.get(dataset_id=dataset_id)
        instance.last_sync_status = status
        self.add(instance)
        return
