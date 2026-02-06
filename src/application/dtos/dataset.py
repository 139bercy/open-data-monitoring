from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.datasets.value_objects import DatasetQuality


@dataclass
class DatasetDTO:
    buid: str
    slug: str
    page: str
    publisher: str
    created: datetime
    modified: datetime
    published: bool
    restricted: bool
    downloads_count: Optional[int]
    api_calls_count: Optional[int]
    quality: DatasetQuality


@dataclass
class DatasetRawDTO:
    dataset_id: UUID
    snapshot: dict
    checksum: str
    downloads_count: Optional[int]
    api_calls_count: Optional[int]
