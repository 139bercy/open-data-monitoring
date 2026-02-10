import abc
from typing import Protocol
from uuid import UUID

from domain.platform.aggregate import Platform


class PlatformRepository(Protocol):  # pragma: no cover
    def save(self, platform: Platform) -> None:
        """Persist a platform aggregate."""
        ...

    def get(self, platform_id: UUID) -> Platform | None:
        """Retrieve a platform by its unique ID."""
        ...

    def all(self) -> list[dict]:
        """Retrieve all registered platforms with their sync history."""
        ...

    def save_sync(self, platform_id: UUID, payload: dict) -> None:
        """Record a new synchronization history entry."""
        ...

    def get_by_domain(self, domain: str) -> Platform | None:
        """Find a platform by its domain name."""
        ...


class PlatformAdapter(Protocol):
    def fetch(self) -> dict:  # pragma: no cover
        """Fetch platform metadata from the source."""
        ...


class DatasetAdapter(abc.ABC):  # pragma: no cover
    @staticmethod
    @abc.abstractmethod
    def find_dataset_id(url: str) -> str | None:
        """Extract dataset ID from a source URL."""
        ...

    @abc.abstractmethod
    def fetch(self, url: str, key: str, dataset_id: str) -> dict:
        """Fetch raw dataset metadata."""
        ...

    @abc.abstractmethod
    def map(self, *args, **kwargs) -> dict:  # pragma: no cover
        """Map raw data to internal representation."""
        ...


class AbstractPlatformAdapterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, platform_type: str, url: str, key: str, slug: str) -> PlatformAdapter:
        """Create a platform-specific metadata adapter."""
        ...


class AbstractDatasetAdapterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, platform_type: str) -> DatasetAdapter:
        """Create a platform-specific dataset adapter."""
        ...
