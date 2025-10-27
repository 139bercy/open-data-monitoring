"""
Router pour les endpoints common
"""

from fastapi import APIRouter, HTTPException

from application.handlers import get_publishers_stats
from interfaces.api.schemas.publishers import PublishersResponse, PublisherStats
from settings import app as domain_app

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/publishers", response_model=PublishersResponse)
async def get_publishers_endpoint():
    """
    Récupère la liste des publishers avec leurs statistiques.

    Équivalent de la commande CLI: `app common get-publishers`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    try:
        # Utilise le handler DDD-compliant avec la nouvelle méthode repository
        publishers_data = get_publishers_stats(domain_app)

        # Transform raw data to Pydantic models
        publishers = [
            PublisherStats(publisher=pub["publisher"], dataset_count=pub["dataset_count"]) for pub in publishers_data
        ]

        return PublishersResponse(publishers=publishers, total_publishers=len(publishers))

    except Exception as e:
        # TODO: Ajouter un système d'exceptions API structuré
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des publishers: {str(e)}",
        )
