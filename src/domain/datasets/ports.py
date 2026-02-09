import abc
from uuid import UUID

from domain.datasets.aggregate import Dataset
from domain.datasets.value_objects import DatasetVersionParams


class AbstractDatasetRepository(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def add(self, dataset: Dataset) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def add_version(self, params: "DatasetVersionParams") -> None:
        """Add a new version of a dataset.

        Args:
            params: DatasetVersionParams containing all version data
        """
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
