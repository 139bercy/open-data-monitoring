from uuid import uuid4

from application.dtos.dataset import DatasetDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import DatasetAdapter
from exceptions import WrongPlatformTypeError
from infrastructure.factories.dataset import DatasetAdapterFactory


class DatasetMonitoring:
    def __init__(self, repository: DatasetRepository):
        self.factory: DatasetAdapterFactory = DatasetAdapterFactory()
        self.repository: DatasetRepository = repository

    def add_dataset(self, platform: Platform, dataset: dict) -> Dataset:
        adapter: DatasetAdapter = self.factory.create(platform_type=platform.type)
        try:
            dto: DatasetDTO = adapter.map(**dataset)
            print(dto)
        except TypeError as e:
            raise WrongPlatformTypeError(e)
        dataset = Dataset(
            id=uuid4(),
            buid=dto.buid,
            platform_id=platform.id,
            slug=dto.slug,
            page=dto.page,
            publisher=dto.publisher,
            created=dto.created,
            published=dto.published,
            modified=dto.modified,
            raw=dataset,
        )
        return dataset
