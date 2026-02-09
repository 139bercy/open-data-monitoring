from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.datasets.value_objects import DatasetQuality


@dataclass
class DatasetDTO:
    buid: str
    slug: str
    title: str
    page: str
    publisher: str
    created: datetime
    modified: datetime
    published: bool
    restricted: bool
    quality: DatasetQuality
    downloads_count: int | None = None
    api_calls_count: int | None = None
    views_count: int | None = None
    reuses_count: int | None = None
    followers_count: int | None = None
    popularity_score: float | None = None


@dataclass
class DatasetRawDTO:
    dataset_id: UUID
    snapshot: dict
    checksum: str
    downloads_count: int | None
    api_calls_count: int | None
    views_count: int | None = None
    reuses_count: int | None = None
    followers_count: int | None = None
    popularity_score: float | None = None
