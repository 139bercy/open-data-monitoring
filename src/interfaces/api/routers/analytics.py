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


@router.get("/summary")
async def get_summary_stats():
    """
    Récupère les KPIs globaux pour le tableau de bord de la page d'accueil.
    """
    query = """
    SELECT
        (SELECT COUNT(*) FROM datasets WHERE NOT deleted) as total_datasets,
        (SELECT COALESCE(AVG(health_score), 0) FROM dataset_quality dq
         JOIN datasets d ON d.id = dq.dataset_id WHERE NOT d.deleted) as avg_health_score,
        (SELECT COUNT(DISTINCT publisher) FROM datasets WHERE NOT deleted AND publisher IS NOT NULL AND publisher != '') as total_publishers,
        (SELECT COUNT(*) FROM dataset_quality dq
         JOIN datasets d ON d.id = dq.dataset_id WHERE NOT d.deleted AND dq.health_score < 50) as crises_count,
        (SELECT COUNT(*) FROM platforms) as total_platforms
    """
    result = domain_app.dataset.repository.client.fetchone(query)
    return result
