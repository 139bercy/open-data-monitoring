import datetime
import uuid

from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import (DatasetAdapter, PlatformAdapter,
                                   PlatformRepository)
from infrastructure.dtos.dataset import DatasetDTO, DatasetRawDTO


class InMemoryPlatformRepository(PlatformRepository):
    def __init__(self, db):
        self.db = db
        self.syncs = []

    def save(self, data):
        self.db.append(data)

    def get(self, platform_id: uuid) -> Platform:
        syncs = [item for item in self.syncs if item["platform_id"] == platform_id]
        platform = next((item for item in self.db if item.id == platform_id), None)
        if len(syncs) is not None:
            for sync in syncs:
                platform.add_sync(sync)
        return platform

    def get_by_domain(self, domain) -> Platform:
        return next((item for item in self.db if domain in item.url), None)

    def all(self):
        return self.db

    def save_sync(self, platform_id, payload):
        self.syncs.append({"platform_id": platform_id, **payload})


class InMemoryAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = key
        self.slug = slug

    def fetch(self) -> dict:
        return {
            "timestamp": datetime.datetime.now(),
            "status": "success",
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


class InMemoryDatasetRepository(DatasetRepository):
    def __init__(self, db):
        self.db = db

    def add(self, dataset: Dataset):
        self.db.append(dataset)

    def get(self, dataset_id):
        dataset = next((item for item in self.db if item.id == dataset_id), None)
        return DatasetRawDTO(dataset_id=dataset.id, snapshot=dataset.raw)
