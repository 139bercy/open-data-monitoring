from uuid import uuid4

from application.dtos.dataset import DatasetDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import DatasetAdapter
from infrastructure.factories.dataset import DatasetAdapterFactory
from logger import logger


class DatasetMonitoring:
    def __init__(self, repository: DatasetRepository):
        self.factory: DatasetAdapterFactory = DatasetAdapterFactory()
        self.repository: DatasetRepository = repository

    def add_dataset(self, platform: Platform, dataset: dict) -> Dataset:
        adapter: DatasetAdapter = self.factory.create(platform_type=platform.type)
        try:
            dto: DatasetDTO = adapter.map(**dataset)
            result = Dataset(
                id=uuid4(),
                buid=dto.buid,
                platform_id=platform.id,
                slug=dto.slug,
                page=dto.page,
                publisher=dto.publisher,
                created=dto.created,
                modified=dto.modified,
                published=dto.published,
                restricted=dto.restricted,
                downloads_count=dto.downloads_count,
                api_calls_count=dto.api_calls_count,
                raw=dataset,
            )
            return result
        except TypeError as e:
            logger.error(
                f"{platform.type.upper()} - Dataset '{dataset}' has encoutered an error"
            )
            # logger.error(f"{platform.type.upper()} - {pprint(dataset)}")
