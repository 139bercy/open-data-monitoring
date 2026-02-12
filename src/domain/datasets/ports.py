from __future__ import annotations

import abc
from uuid import UUID

from domain.datasets.aggregate import Dataset
from domain.datasets.value_objects import DatasetVersionParams


class AbstractDatasetRepository(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def add(self, dataset: Dataset) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def add_version(self, params: DatasetVersionParams) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, dataset_id: UUID, include_versions: bool = True) -> Dataset:
        raise NotImplementedError

    @abc.abstractmethod
    def get_checksum_by_buid(self, dataset_buid) -> str | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_buid(self, dataset_buid: str) -> Dataset | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_publishers_stats(self) -> list[dict[str, any]]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_id_by_slug(self, platform_id: UUID, slug: str) -> UUID | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_id_by_slug_globally(self, slug: str) -> UUID | None:
        raise NotImplementedError

    @abc.abstractmethod
    def update_linking(self, dataset: Dataset) -> None:
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
