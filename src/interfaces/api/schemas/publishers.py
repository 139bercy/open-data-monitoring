"""
Schemas Pydantic pour les endpoints publishers
"""

from pydantic import BaseModel, Field


class PublisherStats(BaseModel):
    """Statistiques d'un publisher"""

    publisher: str = Field(description="Nom du publisher", examples=["Mairie de Bordeaux"])
    dataset_count: int = Field(description="Nombre total de datasets pour ce publisher")

    model_config = {"arbitrary_types_allowed": True}


class PublishersResponse(BaseModel):
    """Réponse pour l'endpoint get-publishers"""

    publishers: list[PublisherStats] = Field(description="Liste des statistiques par publisher")
    total_publishers: int = Field(description="Nombre total de publishers trouvés")
