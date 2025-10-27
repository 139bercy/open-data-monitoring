import abc
from typing import Optional
from uuid import UUID

from application.dtos.dataset import DatasetRawDTO
from domain.datasets.aggregate import Dataset


class DatasetRepository(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def add(self, dataset: Dataset) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def add_version(
        self,
        dataset_id: UUID,
        snapshot: dict,
        checksum: str | None,
        downloads_count: int,
        api_calls_count: int,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, dataset_id: UUID) -> DatasetRawDTO:
        raise NotImplementedError

    @abc.abstractmethod
    def get_checksum_by_buid(self, dataset_buid) -> DatasetRawDTO:
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_buid(self, dataset_buid: str) -> Optional[Dataset]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_publishers_stats(self) -> list[dict[str, any]]:
        """Récupère les statistiques des publishers (nom et nombre de datasets)"""
        raise NotImplementedError

    def get_id_by_slug(self, platform_id, slug):
        raise NotImplementedError

    @abc.abstractmethod
    def update_dataset_sync_status(self, platform_id, dataset_id, status):
        raise NotImplementedError
