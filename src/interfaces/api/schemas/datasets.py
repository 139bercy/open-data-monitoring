"""
Schemas Pydantic pour les endpoints datasets
"""

import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class DatasetAPI(BaseModel):
    id: Optional[UUID]
    name: Optional[str] = None
    timestamp: datetime.datetime
    buid: str
    slug: str
    page: str
    publisher: Optional[str]
    created: datetime.datetime
    modified: datetime.datetime
    published: bool
    restricted: bool
    last_sync: Optional[datetime.datetime]
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
    datasets: List[DatasetAPI]
    total_datasets: int
