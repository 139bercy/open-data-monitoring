from uuid import UUID

from fastapi import APIRouter, HTTPException

from application.handlers import create_platform
from interfaces.api.schemas.platforms import (
    PlatformCreateDTO,
    PlatformCreateResponse,
    PlatformDTO,
    PlatformsResponse,
)
from logger import logger
from settings import app as domain_app

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("/", response_model=PlatformsResponse)
@router.get("", response_model=PlatformsResponse)
async def get_platforms():
    """
    Retrieve the list of all configured open data platforms.
    Useful for obtaining platform IDs and tracking synchronization health.
    """
    platforms = domain_app.platform.get_all_platforms()
    return PlatformsResponse(
        platforms=[PlatformDTO.model_validate(p) for p in platforms], total_platforms=len(platforms)
    )


@router.post("/", response_model=PlatformCreateResponse)
@router.post("", response_model=PlatformCreateResponse)
async def create_platform_endpoint(platform: PlatformCreateDTO):
    """
    Register a new open data platform in the system.
    Requires a unique slug and valid base URL.
    """
    platform_id = create_platform(app=domain_app, data=platform.model_dump())
    if not isinstance(platform_id, UUID):
        raise HTTPException(status_code=500, detail="Failed to create platform")

    platform_raw = domain_app.platform.get(platform_id)
    if not platform_raw:
        raise HTTPException(status_code=404, detail="Platform created but not found")

    return PlatformCreateResponse.model_validate(platform_raw)


@router.post("/sync/{id}")
async def sync_platform_endpoint(id: UUID):
    """
    Trigger a manual synchronization for a specific platform.
    This process will discover new datasets and update existing ones.
    """
    try:
        domain_app.platform.sync_platform(platform_id=id)
        return {"status": "success", "message": f"Platform {id} sync started"}
    except Exception as e:
        logger.error(f"Sync failed for platform {id}: {e}")
        raise HTTPException(status_code=404, detail=f"Platform {id} not found or sync failed")
