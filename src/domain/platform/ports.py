import uuid
from typing import Protocol

from domain.platform.aggregate import Platform


class PlatformRepository:  # pragma: no cover
    def save(self, platform: Platform) -> None:
        raise NotImplementedError

    def get(self, platform_id: uuid) -> Platform:
        raise NotImplementedError

    def all(self):
        raise NotImplementedError

    def save_sync(self, platform_id, payload):
        raise NotImplementedError


class PlatformAdapter(Protocol):
    def fetch(self) -> dict:  # pragma: no cover
        raise NotImplementedError


class DatasetAdapter(Protocol):  # pragma: no cover
    @staticmethod
    def find_dataset_id(url):
        raise NotImplementedError

    def fetch(self, url, key, dataset_id):
        raise NotImplementedError

    def map(self, *args, **kwargs) -> dict:  # pragma: no cover
        raise NotImplementedError
