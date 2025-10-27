"""
Schemas Pydantic pour les endpoints publishers
"""

from typing import List

from pydantic import BaseModel


class PublisherStats(BaseModel):
    """Statistiques d'un publisher"""

    publisher: str
    dataset_count: int

    class Config:
        from_attributes = True


class PublishersResponse(BaseModel):
    """Réponse pour l'endpoint get-publishers"""

    publishers: List[PublisherStats]
    total_publishers: int
