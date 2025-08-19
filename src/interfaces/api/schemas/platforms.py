"""
Schemas Pydantic pour les endpoints platforms
"""

from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class PlatformDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    type: str
    url: str
    organization_id: str
    key: Optional[str]
    datasets_count: int
    last_sync: Optional[datetime]
    created_at: Optional[datetime]

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
    platforms: List[PlatformDTO]
    total_platforms: int

    class Config:
        arbitrary_types_allowed = True