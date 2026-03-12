"""
Router pour les endpoints common
"""

from fastapi import APIRouter

from application.use_cases.get_publishers_stats import GetPublishersStatsUseCase
from interfaces.api.schemas.publishers import PublishersResponse, PublisherStats
from settings import PROCONNECT_FEATURE_LEVEL
from settings import app as domain_app

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/features")
async def get_features():
    """
    Retourne l'état des feature flags globaux configurés sur le serveur.
    """
    return {"proconnect": PROCONNECT_FEATURE_LEVEL}


@router.get("/publishers", response_model=PublishersResponse)
async def get_publishers_endpoint():
    """
    Récupère la liste des publishers avec leurs statistiques.

    Équivalent de la commande CLI: `app common get-publishers`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    use_case = GetPublishersStatsUseCase(uow=domain_app.uow)
    output = use_case.handle()
    publishers_data = output.stats

    # Transform raw data to Pydantic models
    publishers = [
        PublisherStats(publisher=pub["publisher"], dataset_count=pub["dataset_count"]) for pub in publishers_data
    ]

    return PublishersResponse(publishers=publishers, total_publishers=len(publishers))
