from eventsourcing.application import Application

from domain.datasets.aggregate import Dataset


class DatasetsMonitoring(Application):
    def __init__(self, factory):
        super().__init__()
        self.adapter = factory

    def create_dataset(self, platform_type, **dataset):
        adapter = self.adapter.create(platform_type)
        dto = adapter.map(**dataset)
        dataset = Dataset(
            buid=dto.buid,
            slug=dto.slug,
            page=dto.page,
            publisher=dto.publisher,
            created=dto.created,
            modified=dto.modified
        )
        self.save(dataset)
        return dataset.id