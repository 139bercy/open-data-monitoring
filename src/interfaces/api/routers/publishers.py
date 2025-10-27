from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from settings import app as domain_app

router = APIRouter(prefix="/publishers", tags=["publishers"])


@router.get("/")
@router.get("")
async def get_publishers(platform_id: Optional[UUID] = None, q: Optional[str] = None, limit: int = 50):
    """
    Retourne la liste des publishers distincts (chaînes), éventuellement filtrée par plateforme et par recherche.
    Forme de réponse adaptée au front: { "items": ["Publisher A", "Publisher B", ...] }
    """
    try:
        where_clauses = ["publisher IS NOT NULL"]
        params: list = []

        if platform_id is not None:
            where_clauses.append("platform_id = %s")
            params.append(str(platform_id))

        if q:
            where_clauses.append("publisher ILIKE %s")
            params.append(f"%{q}%")

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT publisher
            FROM datasets
            WHERE {where_sql}
            GROUP BY publisher
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        params.append(limit)

        rows = domain_app.dataset.repository.client.fetchall(query, tuple(params))
        items = [r["publisher"] for r in rows if r.get("publisher")]
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
