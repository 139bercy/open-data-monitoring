from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from application.handlers import fetch_dataset, find_dataset_id_from_url, find_platform_from_url, upsert_dataset
from application.services.quality_assessment import QualityAssessmentService
from infrastructure.llm.openai_evaluator import OpenAIEvaluator
from interfaces.api.schemas.datasets import (
    DatasetAPI,
    DatasetCreateResponse,
    DatasetDetailAPI,
    DatasetResponse,
    DatasetVersionsResponse,
)
from settings import app as domain_app

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/add", response_model=DatasetCreateResponse)
async def add_dataset(url: str):
    """
    Ajoute un dataset à la base de données à partir de son URL source.
    Supporte ODS (explore/dataset/...) et DataGouv.
    """
    platform = find_platform_from_url(app=domain_app, url=url)
    if not platform:
        raise HTTPException(status_code=404, detail=f"No platform found for URL: {url}")

    dataset_id = find_dataset_id_from_url(app=domain_app, url=url)
    if not dataset_id:
        raise HTTPException(status_code=404, detail=f"Could not extract dataset ID from URL: {url}")

    dataset = fetch_dataset(platform=platform, dataset_id=dataset_id)
    if not dataset or dataset.get("sync_status") == "failed":
        raise HTTPException(status_code=400, detail=f"Failed to fetch dataset metadata from {platform.type}")

    dataset_uuid = upsert_dataset(app=domain_app, platform=platform, dataset=dataset)
    if not dataset_uuid:
        raise HTTPException(status_code=500, detail="Internal error during dataset persistence")

    return {
        "status": "success",
        "id": dataset_uuid,
        "platform_id": platform.id,
        "buid": dataset.get("uid") or dataset.get("id") or dataset.get("dataset_id"),
        "slug": dataset_id,
    }


@router.get("/tests", response_model=DatasetResponse)
async def get_tests():
    """
    Récupère la liste des datasets tests.

    Équivalent de la commande CLI: `app dataset get tests`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    query = """
    SELECT d.*, d.deleted
    FROM datasets d JOIN platforms p ON p.id = d.platform_id
    WHERE d.slug ILIKE '%test%' AND p.type = 'opendatasoft'
    ORDER BY timestamp DESC
    """
    datasets_raw = domain_app.dataset.repository.client.fetchall(query)
    datasets_list = [
        DatasetAPI(
            id=dataset["id"],
            platform_id=dataset["platform_id"],
            timestamp=dataset["timestamp"],
            buid=dataset["buid"],
            slug=dataset["slug"],
            page=dataset["page"],
            publisher=dataset["publisher"],
            published=dataset["published"],
            restricted=dataset["restricted"],
            last_sync=dataset["last_sync"],
            last_sync_status=dataset["last_sync_status"],
            created=dataset["created"],
            modified=dataset["modified"],
            deleted=dataset["deleted"],
        )
        for dataset in datasets_raw
    ]
    return DatasetResponse(datasets=datasets_list, total_datasets=len(datasets_list))


@router.get("/", response_model=DatasetResponse)
@router.get("", response_model=DatasetResponse)
async def list_datasets(
    platform_id: str | None = None,
    publisher: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    modified_from: str | None = None,
    modified_to: str | None = None,
    q: str | None = None,
    sort_by: str = Query(  # noqa: B008
        "modified",
        pattern="^(created|modified|publisher|title|api_calls_count|downloads_count|versions_count|popularity_score|views_count|reuses_count|followers_count)$",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),  # noqa: B008
    page: int = 1,
    page_size: int = 25,
    include_counts: bool = True,
    is_deleted: bool | None = None,
):
    """
    Liste paginée de datasets.
    """
    items, total = domain_app.dataset.repository.search(
        platform_id=platform_id,
        publisher=publisher,
        q=q,
        created_from=created_from,
        created_to=created_to,
        modified_from=modified_from,
        modified_to=modified_to,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )

    return DatasetResponse(datasets=items, total_datasets=total)


@router.get("/{dataset_id}", response_model=DatasetDetailAPI)
async def get_dataset_detail(dataset_id: UUID, include_snapshots: bool = False):
    """
    Détail d'un dataset avec snapshot courant. Optionnellement inclut la liste des snapshots.
    """
    detail = domain_app.dataset.repository.get_detail(dataset_id, include_snapshots)
    if not detail:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return detail


@router.get("/{dataset_id}/versions", response_model=DatasetVersionsResponse)
async def get_dataset_versions(dataset_id: UUID, page: int = 1, page_size: int = 10, include_data: bool = False):
    """
    Liste paginée des versions (snapshots) d'un dataset.
    """
    items, total = domain_app.dataset.repository.get_versions(dataset_id, page, page_size)
    return {"versions": items, "total_versions": total, "page": page, "page_size": page_size}


@router.get("/publisher/{publisher_name}", response_model=DatasetResponse)
async def get_by_publisher(publisher_name: str):
    """
    Récupère la liste des datasets liés à un publisher précis.
    """
    items, total = domain_app.dataset.repository.search(publisher=publisher_name, page_size=1000)
    return DatasetResponse(datasets=items, total_datasets=total)


@router.post("/{dataset_id}/evaluate")
async def evaluate_dataset(dataset_id: UUID):
    """
    Déclenche une évaluation de qualité par LLM pour un dataset.
    """
    # Initialize service (OpenAI by default for now)
    evaluator = OpenAIEvaluator(model_name="gpt-4o-mini")
    service = QualityAssessmentService(evaluator=evaluator, uow=domain_app.uow)

    # Paths to reference docs (should be configurable or standard)
    dcat_path = "docs/quality/dcat_reference.md"
    charter_path = "docs/quality/charter_opendata.md"

    try:
        evaluation = service.evaluate_dataset(
            dataset_id=str(dataset_id), dcat_path=dcat_path, charter_path=charter_path, output="json"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from dataclasses import asdict

    return asdict(evaluation)


@router.get("/{dataset_id}/audit-report")
async def get_audit_report(dataset_id: UUID):
    """
    Génère et télécharge un rapport d'audit qualité au format PDF.
    """
    from fastapi.responses import StreamingResponse

    from application.services.headless_report import PlaywrightReportGenerator

    dataset = domain_app.dataset.repository.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    generator = PlaywrightReportGenerator()
    pdf_buffer = await generator.generate_audit_report(dataset)

    filename = f"audit_report_{dataset.slug}.pdf"

    return StreamingResponse(
        pdf_buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
