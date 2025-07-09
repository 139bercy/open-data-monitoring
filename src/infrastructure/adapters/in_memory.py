import datetime
import uuid
from typing import Optional

from application.dtos.dataset import DatasetDTO, DatasetRawDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.ports import DatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import (DatasetAdapter, PlatformAdapter,
                                   PlatformRepository)
from domain.unit_of_work import UnitOfWork


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
    def find_dataset_id(url):
        raise NotImplementedError

    def fetch(self, url, key, dataset_id):
        raise NotImplementedError

    @staticmethod
    def map(
        id, slug, page, created_at, last_update, published, restricted, *args, **kwargs
    ):
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            page=page,
            publisher="",
            created=created_at,
            modified=last_update,
            published=published,
            restricted=restricted,
            downloads_count=download_count,
            api_calls_count=api_calls_count,
        )
        return dataset


class InMemoryDatasetRepository(DatasetRepository):
    def __init__(self, db):
        self.db = db
        self.versions = []

    def add(self, dataset: Dataset):
        self.db.append(dataset)

    def add_version(
        self,
        dataset_id: uuid.UUID,
        snapshot: dict,
        checksum: str,
        downloads_count: int,
        api_calls_count: int,
    ) -> None:
        self.versions.append(
            {
                "dataset_id": dataset_id,
                "snapshot": snapshot,
                "checksum": checksum,
                "downloads_count": downloads_count,
                "api_calls_count": api_calls_count,
            }
        )

    def get(self, dataset_id):
        dataset = next((item for item in self.db if item.id == dataset_id), None)
        next(
            (
                dataset.add_version(**item)
                for item in self.versions
                if item["dataset_id"] == dataset_id
            ),
            None,
        )
        return dataset

    def get_checksum_by_buid(self, dataset_buid) -> Optional[DatasetRawDTO]:
        dataset = next((item for item in self.db if item.buid == dataset_buid), None)
        if dataset is not None:
            return dataset.checksum
        return

    def get_by_buid(self, dataset_buid: str) -> Optional[Dataset]:
        dataset = next((item for item in self.db if item.buid == dataset_buid), None)
        if dataset is not None:
            return dataset
        return


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self):
        self._platforms = InMemoryPlatformRepository([])
        self._datasets = InMemoryDatasetRepository([])
        self._in_transaction = False
        self._pending_changes = []

    def __enter__(self):
        self._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_transaction = False
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        if self._in_transaction:
            self._pending_changes = []

    def rollback(self):
        if self._in_transaction:
            self._pending_changes = []

    @property
    def platforms(self) -> InMemoryPlatformRepository:
        return self._platforms

    @property
    def datasets(self) -> InMemoryDatasetRepository:
        return self._datasets
