"""
Schemas Pydantic pour les endpoints platforms
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PlatformSync(BaseModel):
    platform_id: UUID
    timestamp: datetime
    status: str
    datasets_count: int


class PlatformDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    type: str
    url: str
    organization_id: str
    key: str | None
    datasets_count: int
    last_sync: datetime | None
    created_at: datetime | None
    last_sync_status: str | None = None
    syncs: list[PlatformSync] | None = None

    class Config:
        arbitrary_types_allowed = True


class PlatformCreateDTO(BaseModel):
    name: str
    slug: str
    organization_id: str
    type: str
    url: str
    key: str


class PlatformCreateResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    type: str
    url: str
    key: str


class PlatformsResponse(BaseModel):
    platforms: list[PlatformDTO]
    total_platforms: int

    class Config:
        arbitrary_types_allowed = True
