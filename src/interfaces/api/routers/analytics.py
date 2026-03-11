from fastapi import APIRouter, Depends

from interfaces.api.dependencies import get_current_user
from settings import app as domain_app

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/direction-health")
async def get_direction_health():
    """
    Récupère les statistiques de santé agrégées par Direction.
    Ces données alimentent la Heatmap de la "Salle de Crise".
    """
    query = """
    SELECT
        direction,
        score_global as score,
        unhealthy_count as crises,
        dataset_count as count
    FROM direction_health_stats_view
    ORDER BY score_global DESC
    """
    # Use the database client from the repository
    results = domain_app.dataset.repository.client.fetchall(query)

    # Return raw results; FastAPI handles JSON conversion
    return results
