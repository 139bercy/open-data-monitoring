import datetime
import uuid

from domain.platform.ports import PlatformAdapter, DatasetAdapter, PlatformRepository
from infrastructure.dtos.dataset import DatasetDTO


class InMemoryPlatformRepository(PlatformRepository):
    def __init__(self, db):
        self.db = db

    def save(self, data):
        self.db.append(data)

    def get(self, platform_id: uuid):
        return next((item for item in self.db if item.id == platform_id), None)

    def all(self):
        return self.db


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
            modified=last_update,
        )
        return dataset
