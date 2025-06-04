import abc

from domain.datasets.aggregate import Dataset
from infrastructure.dtos.dataset import DatasetRawDTO


class DatasetRepository(abc.ABC):  # pragma: no cover
    def add(self, dataset: Dataset) -> None:
        raise NotImplementedError

    def get(self, dataset_id) -> DatasetRawDTO:
        raise NotImplementedError
