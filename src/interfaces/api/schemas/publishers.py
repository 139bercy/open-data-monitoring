"""
Schemas Pydantic pour les endpoints publishers
"""

from pydantic import BaseModel
from typing import List


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
