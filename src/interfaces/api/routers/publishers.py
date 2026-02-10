from uuid import UUID

from fastapi import APIRouter

from settings import app as domain_app

router = APIRouter(prefix="/publishers", tags=["publishers"])


@router.get("/")
@router.get("")
async def get_publishers(platform_id: UUID | None = None, q: str | None = None, limit: int = 50):
    """
    Retrieve the list of unique publishers (organizations) from indexed datasets.
    Supports filtering by platform and name search.
    """
    items = domain_app.dataset.repository.list_publishers(platform_id=platform_id, q=q, limit=limit)
    return {"items": items}
