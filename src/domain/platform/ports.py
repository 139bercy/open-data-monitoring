import abc
from typing import Protocol
from uuid import UUID

from domain.platform.aggregate import Platform


class PlatformRepository(Protocol):  # pragma: no cover
    def save(self, platform: Platform) -> None:
        raise NotImplementedError

    def get(self, platform_id: UUID) -> Platform:
        raise NotImplementedError

    def all(self):
        raise NotImplementedError

    def save_sync(self, platform_id, payload):
        raise NotImplementedError

    def get_by_domain(self, domain) -> Platform:
        raise NotImplementedError


class PlatformAdapter(Protocol):
    def fetch(self) -> dict:  # pragma: no cover
        raise NotImplementedError


class DatasetAdapter(abc.ABC):  # pragma: no cover
    @staticmethod
    def find_dataset_id(url):
        raise NotImplementedError

    def fetch(self, url, key, dataset_id):
        raise NotImplementedError

    def map(self, *args, **kwargs) -> dict:  # pragma: no cover
        raise NotImplementedError


class AbstractPlatformAdapterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, platform_type: str, url: str, key: str, slug: str) -> PlatformAdapter:
        raise NotImplementedError


class AbstractDatasetAdapterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, platform_type: str) -> DatasetAdapter:
        raise NotImplementedError
