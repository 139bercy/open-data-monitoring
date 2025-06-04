from uuid import uuid4

from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.ports import DatasetAdapter
from infrastructure.factories.dataset import DatasetAdapterFactory


class DatasetMonitoring:
    def __init__(self, factory: DatasetAdapterFactory, repository: DatasetRepository):
        self.factory: DatasetAdapterFactory = factory
        self.repository: DatasetRepository = repository
        self.adapter: DatasetAdapter or None = None

    def set_adapter(self, platform_type):
        self.adapter = self.factory.create(platform_type)

    def add_dataset(self, platform_type, dataset):
        adapter = self.factory.create(platform_type)
        dto = adapter.map(**dataset)
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
