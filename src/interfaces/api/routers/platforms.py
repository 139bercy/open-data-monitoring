from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from settings import app as domain_app
from application.handlers import create_platform
from interfaces.api.schemas.platforms import PlatformsResponse, PlatformDTO, PlatformCreateDTO, PlatformCreateResponse

router = APIRouter(prefix="/platforms", tags=["platforms"])

@router.get("/", response_model=PlatformsResponse)
@router.get("", response_model=PlatformsResponse)
async def get_platforms():
    """
    Récupère la liste des plateformes Open Data.

    Équivalent de la commande CLI: `app platform all`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    try:
        platforms_raw = domain_app.platform.get_all_platforms()

        platforms = _bind_to_platform_model(platforms_raw)

        platforms_DTO = [PlatformDTO(**vars(p)) for p in platforms]
        
        return PlatformsResponse(
            platforms=platforms_DTO,
            total_platforms=len(platforms)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PlatformCreateResponse)
@router.post("", response_model=PlatformCreateResponse)
async def create_platform_endpoint(platform: PlatformCreateDTO):
    """
    Crée une nouvelle plateforme Open Data.

    Équivalent de la commande CLI: `app platform create`
    """
    try:
        platform_id = create_platform(app=domain_app, data=platform.model_dump())
        if type(platform_id) is not UUID:
            raise HTTPException(status_code=500, detail="Failed to create platform")

        platform_raw = domain_app.platform.get(platform_id)
    
        return PlatformCreateResponse(
            id=platform_raw.id,
            name=platform_raw.name,
            slug=platform_raw.slug,
            type=platform_raw.type,
            url=platform_raw.url,
            key=platform_raw.key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " - " + str(platform))

@router.post("/sync/{id}")
async def sync_platform_endpoint(id: UUID):
    """
    Synchronise une plateforme Open Data.

    Équivalent de la commande CLI: `app platform sync`
    """
    try:
        domain_app.platform.sync_platform(platform_id=id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _bind_to_platform_model(platforms_raw) -> List[PlatformDTO]:
    if not platforms_raw:
        return []
    
    return [
        PlatformDTO(
            id=UUID(platform["id"]) if isinstance(platform["id"], str) else platform["id"],
            name=platform["name"],
            slug=platform["slug"],
            type=platform["type"],
            url=platform["url"],
            organization_id=platform["organization_id"],
            key=platform.get("key"),
            datasets_count=platform.get("datasets_count"),
            last_sync=platform.get("last_sync"),
            created_at=platform.get("created_at")
        ) for platform in platforms_raw
    ]