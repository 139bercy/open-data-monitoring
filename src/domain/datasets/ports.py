import abc
from typing import Optional
from uuid import UUID

from domain.datasets.aggregate import Dataset


class AbstractDatasetRepository(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def add(self, dataset: Dataset) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def add_version(
        self,
        dataset_id: UUID,
        snapshot: dict,
        checksum: Optional[str],
        title: str,
        downloads_count: Optional[int] = None,
        api_calls_count: Optional[int] = None,
        views_count: Optional[int] = None,
        reuses_count: Optional[int] = None,
        followers_count: Optional[int] = None,
        popularity_score: Optional[float] = None,
        diff: Optional[dict] = None,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, dataset_id: UUID) -> Dataset:
        raise NotImplementedError

    @abc.abstractmethod
    def get_checksum_by_buid(self, dataset_buid) -> Optional[str]:
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

    @abc.abstractmethod
    def update_dataset_state(self, dataset: Dataset) -> None:
        raise NotImplementedError
