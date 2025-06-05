from uuid import uuid4

from application.dtos.dataset import DatasetDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.ports import DatasetAdapter
from infrastructure.factories.dataset import DatasetAdapterFactory


class DatasetMonitoring:
    def __init__(self, factory: DatasetAdapterFactory, repository: DatasetRepository):
        self.factory: DatasetAdapterFactory = factory
        self.repository: DatasetRepository = repository

    def add_dataset(self, platform_type: str, dataset: dict) -> Dataset:
        adapter: DatasetAdapter = self.factory.create(platform_type)
        dto: DatasetDTO = adapter.map(**dataset)
        dataset = Dataset(
            id=uuid4(),
            buid=dto.buid,
            slug=dto.slug,
            page=dto.page,
            publisher=dto.publisher,
            created=dto.created,
            modified=dto.modified,
            raw=dataset,
        )
        return dataset
