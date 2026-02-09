"""
Schemas Pydantic pour les endpoints datasets
"""

import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetAPI(BaseModel):
    id: UUID | None = Field(None, description="Identifiant unique du dataset")
    name: str | None = Field(None, description="Nom humain du dataset", examples=["Consommation d'eau"])
    timestamp: datetime.datetime = Field(description="Date du snapshot")
    buid: str = Field(description="Identifiant métier unique (Business ID)", examples=["ods:eau-2023"])
    slug: str = Field(description="Slug unique", examples=["consommation-eau"])
    page: str = Field(description="URL de la page source", examples=["https://data.com/dataset/eau"])
    publisher: str | None = Field(None, description="Nom du producteur de données", examples=["Ville de Paris"])
    created: datetime.datetime = Field(description="Date de création initiale")
    modified: datetime.datetime = Field(description="Date de dernière modification sur la plateforme")
    published: bool = Field(description="Indique si le dataset est public")
    restricted: bool = Field(description="Indique si l'accès est restreint")
    deleted: bool = Field(False, description="Indique si le dataset est marqué comme supprimé")
    last_sync: datetime.datetime | None = Field(None, description="Dernière date de synchronisation")
    last_sync_status: str = Field(description="Statut de la dernière sync (success, failed)")


class DatasetCreateResponse(BaseModel):
    id: UUID = Field(description="Nouvel identifiant généré")
    name: str = Field(description="Nom du dataset créé")
    timestamp: str = Field(description="Timestamp de création")
    buid: str = Field(description="BUID généré")
    slug: str = Field(description="Slug généré")
    organization_id: str = Field(description="ID de l'organisation parente")
    type: str = Field(description="Type de plateforme")
    url: str = Field(description="URL source")
    key: str = Field(description="Clé API utilisée")


class DatasetResponse(BaseModel):
    datasets: list[DatasetAPI]
    total_datasets: int
