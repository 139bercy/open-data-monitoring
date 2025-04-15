import datetime

from domain.platform.ports import PlatformAdapter, DatasetAdapter
from infrastructure.dtos.dataset import DatasetDTO


class InMemoryAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = key
        self.slug = slug

    def fetch(self) -> dict:
        return {
            "timestamp": datetime.datetime.now(),
            "status": "Success",
            "datasets_count": 10,
        }


class InMemoryDatasetAdapter(DatasetAdapter):
    @staticmethod
    def map(id, slug, page, created_at, last_update, *args, **kwargs):
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            page=page,
            publisher="",
            created=created_at,
            modified=last_update
        )
        return dataset
