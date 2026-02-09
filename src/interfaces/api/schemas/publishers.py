"""
Schemas Pydantic pour les endpoints publishers
"""

from pydantic import BaseModel


class PublisherStats(BaseModel):
    """Statistiques d'un publisher"""

    publisher: str
    dataset_count: int

    model_config = {"arbitrary_types_allowed": True}


class PublishersResponse(BaseModel):
    """Réponse pour l'endpoint get-publishers"""

    publishers: list[PublisherStats]
    total_publishers: int
