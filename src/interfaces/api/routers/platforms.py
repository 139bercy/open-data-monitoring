from uuid import UUID

from fastapi import APIRouter, HTTPException

from application.handlers import create_platform
from interfaces.api.schemas.platforms import PlatformCreateDTO, PlatformCreateResponse, PlatformDTO, PlatformsResponse
from settings import app as domain_app

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("/", response_model=PlatformsResponse)
@router.get("", response_model=PlatformsResponse)
async def get_platforms():
    """
    Récupère la liste des plateformes Open Data.

    Équivalent de la commande CLI: `app platform all`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    platforms_raw = domain_app.platform.get_all_platforms()
    platforms_dto = _bind_to_platform_model(platforms_raw)
    return PlatformsResponse(platforms=platforms_dto, total_platforms=len(platforms_dto))


@router.post("/", response_model=PlatformCreateResponse)
@router.post("", response_model=PlatformCreateResponse)
async def create_platform_endpoint(platform: PlatformCreateDTO):
    """
    Crée une nouvelle plateforme Open Data.

    Équivalent de la commande CLI: `app platform create`
    """
    platform_id = create_platform(app=domain_app, data=platform.model_dump())
    if not isinstance(platform_id, UUID):
        raise HTTPException(status_code=500, detail="Failed to create platform")

    platform_raw = domain_app.platform.get(platform_id)

    return PlatformCreateResponse(
        id=platform_raw.id,
        name=platform_raw.name,
        slug=str(platform_raw.slug),
        type=str(platform_raw.type),
        url=str(platform_raw.url),
        key=platform_raw.key,
    )


@router.post("/sync/{id}")
async def sync_platform_endpoint(id: UUID):
    """
    Synchronise une plateforme Open Data.

    Équivalent de la commande CLI: `app platform sync`
    """
    domain_app.platform.sync_platform(platform_id=id)
    return {"status": "success", "message": f"Platform {id} sync started"}


def _bind_to_platform_model(platforms_raw) -> list[PlatformDTO]:
    if not platforms_raw:
        return []

    return [
        PlatformDTO(
            id=p.id,
            name=p.name,
            slug=str(p.slug),
            type=str(p.type),
            url=str(p.url),
            organization_id=p.organization_id,
            key=p.key,
            datasets_count=p.datasets_count,
            last_sync=p.last_sync,
            created_at=p.created_at,
            last_sync_status=str(p.last_sync_status) if p.last_sync_status else None,
            syncs=p.syncs,
        )
        for p in platforms_raw
    ]
