import uuid
from typing import Protocol

from domain.platform.aggregate import Platform


class PlatformRepository:       # pragma: no cover
    def save(self, platform: Platform) -> None:
        raise NotImplementedError

    def get(self, platform_id: uuid) -> Platform:
        raise NotImplementedError

    def all(self):
        raise NotImplementedError


class PlatformAdapter(Protocol):
    def fetch(self) -> dict:  # pragma: no cover
        raise NotImplementedError


class DatasetAdapter(Protocol):
    def map(self, *args, **kwargs) -> dict:  # pragma: no cover
        raise NotImplementedError
