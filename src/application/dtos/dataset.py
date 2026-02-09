from dataclasses import dataclass
from datetime import datetime
from typing import Optional
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
    downloads_count: Optional[int] = None
    api_calls_count: Optional[int] = None
    views_count: Optional[int] = None
    reuses_count: Optional[int] = None
    followers_count: Optional[int] = None
    popularity_score: Optional[float] = None


@dataclass
class DatasetRawDTO:
    dataset_id: UUID
    snapshot: dict
    checksum: str
    downloads_count: Optional[int]
    api_calls_count: Optional[int]
    views_count: Optional[int] = None
    reuses_count: Optional[int] = None
    followers_count: Optional[int] = None
    popularity_score: Optional[float] = None
