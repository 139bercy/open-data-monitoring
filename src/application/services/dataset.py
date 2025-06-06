from uuid import uuid4
from uuid import UUID

from application.dtos.dataset import DatasetDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import DatasetAdapter
from infrastructure.factories.dataset import DatasetAdapterFactory


class WrongPlatformTypeError(Exception):
    pass


class DatasetMonitoring:
    def __init__(self, repository: DatasetRepository):
        self.factory: DatasetAdapterFactory = DatasetAdapterFactory()
        self.repository: DatasetRepository = repository

    def add_dataset(self, platform: Platform, dataset: dict) -> Dataset:
        adapter: DatasetAdapter = self.factory.create(platform_type=platform.type)
        try:
            dto: DatasetDTO = adapter.map(**dataset)
        except TypeError:
            raise WrongPlatformTypeError()
        dataset = Dataset(
            id=uuid4(),
            buid=dto.buid,
            platform_id=platform.id,
            slug=dto.slug,
            page=dto.page,
            publisher=dto.publisher,
            created=dto.created,
            modified=dto.modified,
            raw=dataset,
        )
        return dataset
