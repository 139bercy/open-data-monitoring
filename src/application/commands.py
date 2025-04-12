from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreatePlatform:
    name: str
    slug: str
    organization_id: str
    type: str
    url: str
    key: str


@dataclass
class SyncPlatform:
    id: UUID
