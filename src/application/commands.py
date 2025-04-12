from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreatePlatform:
    name: str
    type: str
    url: str
    key: str


@dataclass
class SyncPlatform:
    id: UUID
