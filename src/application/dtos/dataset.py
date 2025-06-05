from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DatasetDTO:
    buid: str
    slug: str
    page: str
    publisher: str
    created: datetime
    modified: datetime


@dataclass
class DatasetRawDTO:
    dataset_id: UUID
    snapshot: dict
    checksum: str
