"""
Schemas Pydantic pour les endpoints platforms
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlatformSync(BaseModel):
    platform_id: UUID = Field(description="Identifiant unique de la plateforme")
    timestamp: datetime = Field(description="Date et heure de la synchronisation")
    status: str = Field(description="Statut de la synchronisation (success, failed, etc.)")
    datasets_count: int = Field(description="Nombre de datasets récupérés lors de cette sync")


class PlatformDTO(BaseModel):
    id: UUID = Field(description="Identifiant unique de la plateforme")
    name: str = Field(description="Nom de la plateforme", examples=["Data Sud"])
    slug: str = Field(description="Slug unique de la plateforme", examples=["data-sud"])
    type: str = Field(description="Type de plateforme (opendatasoft, datagouv)", examples=["opendatasoft"])
    url: str = Field(description="URL de base de l'API de la plateforme", examples=["https://data.sud.fr"])
    organization_id: str = Field(description="ID de l'organisation sur la plateforme")
    key: str | None = Field(None, description="Clé API (masquée dans les réponses publiques)")
    datasets_count: int = Field(0, description="Nombre total de datasets référencés")
    last_sync: datetime | None = Field(None, description="Date de la dernière synchronisation")
    created_at: datetime | None = Field(None, description="Date de création dans le monitoring")
    last_sync_status: str | None = Field(None, description="Dernier statut de sync")
    syncs: list[PlatformSync] | None = Field(None, description="Historique des synchronisations")

    model_config = {"arbitrary_types_allowed": True}


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
    model_config = {"arbitrary_types_allowed": True}


class PlatformsResponse(BaseModel):
    platforms: list[PlatformDTO]
    total_platforms: int

    model_config = {"arbitrary_types_allowed": True}
