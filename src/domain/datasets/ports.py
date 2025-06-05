import abc
from uuid import UUID

from application.dtos.dataset import DatasetRawDTO
from domain.datasets.aggregate import Dataset


class DatasetRepository(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def add(self, dataset: Dataset) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, dataset_id: UUID) -> DatasetRawDTO:
        raise NotImplementedError
