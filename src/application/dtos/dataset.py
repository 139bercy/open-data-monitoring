from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class DatasetDTO:
    id: UUID
    buid: str
    slug: str
    page: str
    publisher: str
    created: datetime
    modified: datetime
    raw: dict


@dataclass
class DatasetRawDTO:
    dataset_id: UUID
    snapshot: dict
    checksum: str
