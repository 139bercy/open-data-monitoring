from typing import Protocol


class PlatformAdapter(Protocol):
    def fetch(self) -> dict:  # pragma: no cover
        raise NotImplementedError


class DatasetAdapter(Protocol):
    def map(self, *args, **kwargs) -> dict:  # pragma: no cover
        raise NotImplementedError
