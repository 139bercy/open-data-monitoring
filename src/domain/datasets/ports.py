import abc
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
        checksum: str | None,
        title: str,
        downloads_count: int | None = None,
        api_calls_count: int | None = None,
        views_count: int | None = None,
        reuses_count: int | None = None,
        followers_count: int | None = None,
        popularity_score: float | None = None,
        diff: dict | None = None,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, dataset_id: UUID) -> Dataset:
        raise NotImplementedError

    @abc.abstractmethod
    def get_checksum_by_buid(self, dataset_buid) -> str | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_buid(self, dataset_buid: str) -> Dataset | None:
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
