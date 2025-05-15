from domain.datasets.aggregate import Dataset
from uuid import uuid4


class DatasetsMonitoring:
    def __init__(self, factory):
        self.adapter = factory

    def create_dataset(self, platform_type, **dataset):
        adapter = self.adapter.create(platform_type)
        dto = adapter.map(**dataset)
        dataset = Dataset(
            id=uuid4(),
            buid=dto.buid,
            slug=dto.slug,
            page=dto.page,
            publisher=dto.publisher,
            created=dto.created,
            modified=dto.modified,
        )
        return dataset
