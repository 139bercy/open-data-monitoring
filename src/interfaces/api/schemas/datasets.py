"""
Schemas Pydantic pour les endpoints datasets
"""

import datetime
from uuid import UUID

from pydantic import BaseModel


class DatasetAPI(BaseModel):
    id: UUID | None
    name: str | None = None
    timestamp: datetime.datetime
    buid: str
    slug: str
    page: str
    publisher: str | None
    created: datetime.datetime
    modified: datetime.datetime
    published: bool
    restricted: bool
    deleted: bool = False
    last_sync: datetime.datetime | None
    last_sync_status: str


class DatasetCreateResponse(BaseModel):
    id: UUID
    name: str
    timestamp: str
    buid: str
    slug: str
    organization_id: str
    type: str
    url: str
    key: str


class DatasetResponse(BaseModel):
    datasets: list[DatasetAPI]
    total_datasets: int
