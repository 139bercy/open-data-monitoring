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

    @abc.abstractmethod
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
        """Search datasets with filters, sorting and pagination."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_detail(self, dataset_id: UUID, include_snapshots: bool = False) -> dict | None:
        """Get full dataset details including current snapshot and optionally history."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_versions(self, dataset_id: UUID, page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
        """Get paginated version history for a dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_publishers(self, platform_id: UUID | None = None, q: str | None = None, limit: int = 50) -> list[str]:
        """Get a list of distinct publishers, optionally filtered by platform or name."""
        raise NotImplementedError
