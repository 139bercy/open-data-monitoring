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
    def add_version(self, dataset_id: UUID, snapshot: dict, checksum: str) -> None:
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
