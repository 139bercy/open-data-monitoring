from dataclasses import dataclass
from uuid import UUID


@dataclass
class DatasetDTO:
    buid: str
    slug: str
    page: str
    publisher: str
    created: str
    modified: str


@dataclass
class DatasetRawDTO:
    dataset_id: UUID
    snapshot: dict
    checksum: str
