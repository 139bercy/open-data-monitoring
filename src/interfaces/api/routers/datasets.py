"""
Router pour les endpoints datasets (STUB)
TODO: Implémenter les endpoints dataset
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from application.handlers import fetch_dataset, find_dataset_id_from_url, find_platform_from_url, upsert_dataset
from application.services.quality_assessment import QualityAssessmentService
from exceptions import DatasetHasNotChanged, DatasetUnreachableError
from infrastructure.llm.openai_evaluator import OpenAIEvaluator
from interfaces.api.schemas.datasets import DatasetAPI, DatasetCreateResponse, DatasetResponse
from logger import logger
from settings import app as domain_app

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/add", response_model=DatasetCreateResponse)
async def add_dataset(url: str):
    """
    Ajoute un dataset à la base de données.
    """
    platform = find_platform_from_url(app=domain_app, url=url)
    dataset_id = find_dataset_id_from_url(app=domain_app, url=url)
    if dataset_id is None:
        logger.warning(f"Dataset not found for url: {url}")
        return
    dataset = fetch_dataset(platform=platform, dataset_id=dataset_id)
    try:
        upsert_dataset(app=domain_app, platform=platform, dataset=dataset)
    except DatasetHasNotChanged as e:
        logger.info(f"{platform.type.upper()} - {dataset_id} - {e}")
    except DatasetUnreachableError:
        pass


@router.get("/tests", response_model=DatasetResponse)
async def get_tests():
    """
    Récupère la liste des datasets tests.

    Équivalent de la commande CLI: `app dataset get tests`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    try:
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
                timestamp=dataset["timestamp"],
                buid=dataset["buid"],
                slug=dataset["slug"],
                page=dataset["page"],
                publisher=dataset["publisher"],
                published=dataset["published"],
                restricted=dataset["restricted"],
                last_sync=dataset["last_sync"],
                last_sync_status=["last_sync_status"],
                created=dataset["created"],
                modified=dataset["modified"],
                deleted=dataset["deleted"],
            )
            for dataset in datasets_raw
        ]
        return DatasetResponse(datasets=datasets_list, total_datasets=len(datasets_list))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
@router.get("")
async def list_datasets(
    platform_id: str | None = None,
    publisher: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    modified_from: str | None = None,
    modified_to: str | None = None,
    q: str | None = None,
    sort_by: str = Query(
        "modified",
        pattern="^(created|modified|publisher|title|api_calls_count|downloads_count|versions_count)$",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 25,
    include_counts: bool = True,
):
    """
    Liste paginée de datasets. Implémentation minimale pour le front UC1.
    - Recherche ILIKE uniquement sur slug (q)
    - Filtres basiques platform_id/publisher/created/modified
    - Tri limité sur created/modified/publisher
    - include_counts ignoré pour l'instant (à implémenter avec dataset_versions)
    """
    try:
        where_clauses = ["TRUE"]
        params: list = []

        if platform_id:
            where_clauses.append("platform_id = %s")
            params.append(platform_id)
        if publisher:
            where_clauses.append("publisher = %s")
            params.append(publisher)
        if q:
            where_clauses.append("slug ILIKE %s")
            params.append(f"%{q}%")
        if created_from:
            where_clauses.append("created >= %s")
            params.append(created_from)
        if created_to:
            where_clauses.append("created <= %s")
            params.append(created_to)
        if modified_from:
            where_clauses.append("modified >= %s")
            params.append(modified_from)
        if modified_to:
            where_clauses.append("modified <= %s")
            params.append(modified_to)

        where_sql = " AND ".join(where_clauses)

        # Count
        count_query = f"SELECT COUNT(*) AS cnt FROM datasets WHERE {where_sql}"
        total_rows = domain_app.dataset.repository.client.fetchall(count_query, tuple(params))
        total = int(total_rows[0]["cnt"]) if total_rows else 0

        # Sorting (NULL-safe): treat NULL as 0 for counts, and as '' for text
        sort_column = (
            sort_by
            if sort_by
            in (
                "created",
                "modified",
                "publisher",
                "title",
                "api_calls_count",
                "downloads_count",
            )
            else "modified"
        )
        sort_dir = "DESC" if order.lower() != "asc" else "ASC"
        if sort_column == "title":
            order_sql = "COALESCE(title, '')"
        elif sort_column == "api_calls_count":
            order_sql = "COALESCE(lv.api_calls_count, 0)"
        elif sort_column == "downloads_count":
            order_sql = "COALESCE(lv.downloads_count, 0)"
        elif sort_column == "versions_count":
            order_sql = "COALESCE(vc.versions_count, 0)"
        elif sort_column == "publisher":
            order_sql = "COALESCE(publisher, '')"
        else:
            order_sql = sort_column

        # Pagination
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size

        # Latest snapshot per dataset to derive a title and counts (works for datagouv and opendatasoft shapes)
        list_query = f"""
            WITH latest_versions AS (
                SELECT DISTINCT ON (dataset_id) dataset_id, snapshot, downloads_count, api_calls_count, timestamp
                FROM dataset_versions
                ORDER BY dataset_id, timestamp DESC
            ),
            version_counts AS (
                SELECT dataset_id, COUNT(*) AS versions_count
                FROM dataset_versions
                GROUP BY dataset_id
            ),
            latest_quality AS (
                SELECT DISTINCT ON (dataset_id) dataset_id, has_description, is_slug_valid, evaluation_results
                FROM dataset_quality
                ORDER BY dataset_id, timestamp DESC
            )
            SELECT d.id,
                   d.platform_id,
                   d.publisher,
                   d.created,
                   d.modified,
                   d.restricted,
                   d.published,
                   d.slug,
                   d.page,
                   COALESCE(
                       (lv.snapshot ->> 'title'),
                       (lv.snapshot -> 'metas' ->> 'title')
                   ) AS title,
                   lv.api_calls_count AS api_calls_count,
                   lv.downloads_count AS downloads_count,
                   COALESCE(vc.versions_count, 0) AS versions_count, 
                   d.last_sync, 
                   d.last_sync_status, 
                   d.deleted,
                   dq.has_description as has_description,
                   dq.is_slug_valid as is_slug_valid,
                   dq.evaluation_results as evaluation_results
            FROM datasets d
            LEFT JOIN latest_versions lv ON lv.dataset_id = d.id
            LEFT JOIN version_counts vc ON vc.dataset_id = d.id
            LEFT JOIN latest_quality dq ON d.id = dq.dataset_id
            WHERE {where_sql}
            ORDER BY {order_sql} {sort_dir}
            LIMIT %s OFFSET %s
        """
        list_params = params + [page_size, offset]
        rows = domain_app.dataset.repository.client.fetchall(list_query, tuple(list_params))

        items = [
            {
                "id": r["id"],
                "platform_id": r["platform_id"],
                "publisher": r.get("publisher"),
                "title": r.get("title"),
                "created": r["created"].isoformat() if r.get("created") else None,
                "modified": r["modified"].isoformat() if r.get("modified") else None,
                "restricted": r.get("restricted"),
                "published": r.get("published"),
                "downloads_count": r.get("downloads_count"),
                "api_calls_count": r.get("api_calls_count"),
                "versions_count": r.get("versions_count"),
                "page": r.get("page"),
                "last_sync": r.get("last_sync"),
                "last_sync_status": r.get("last_sync_status"),
                "deleted": r.get("deleted"),
                "has_description": r.get("has_description"),
                "quality": {
                    "has_description": r.get("has_description"),
                    "is_slug_valid": r.get("is_slug_valid"),
                    "evaluation_results": r.get("evaluation_results"),
                }
            }
            for r in rows
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}")
async def get_dataset_detail(dataset_id: UUID, include_snapshots: bool = False):
    """
    Détail d'un dataset avec snapshot courant. Optionnellement inclut la liste des snapshots.
    """
    try:
        # Base dataset
        ds_query = (
            "SELECT d.id, d.platform_id, d.buid, d.slug, d.page, d.publisher, d.created, d.modified, d.published, d.restricted, d.deleted, "
            "dq.has_description, dq.is_slug_valid, dq.evaluation_results "
            "FROM datasets d "
            "LEFT JOIN ("
            "    SELECT DISTINCT ON (dataset_id) dataset_id, has_description, is_slug_valid, evaluation_results "
            "    FROM dataset_quality "
            "    ORDER BY dataset_id, timestamp DESC"
            ") dq ON d.id = dq.dataset_id "
            "WHERE  d.id = %s"
        )
        rows = domain_app.dataset.repository.client.fetchall(ds_query, (str(dataset_id),))
        if not rows:
            raise HTTPException(status_code=404, detail="Dataset not found")
        d = rows[0]

        # Latest version for current snapshot
        cur_query = (
            "SELECT id, timestamp, downloads_count, api_calls_count, snapshot, "
            "COALESCE(snapshot->>'title', snapshot->'metas'->>'title') AS title "
            "FROM dataset_versions WHERE dataset_id = %s ORDER BY timestamp DESC LIMIT 1"
        )
        cur_rows = domain_app.dataset.repository.client.fetchall(cur_query, (str(dataset_id),))
        current_snapshot = None
        if cur_rows:
            r = cur_rows[0]
            current_snapshot = {
                "id": r["id"],
                "timestamp": r["timestamp"].isoformat() if r.get("timestamp") else None,
                "downloads_count": r.get("downloads_count"),
                "api_calls_count": r.get("api_calls_count"),
                "page": d.get("page"),
                "title": r.get("title"),
                "data": r.get("snapshot"),
            }

        # Optional snapshots list (not paginated here, front uses /versions normally)
        snapshots = None
        if include_snapshots:
            list_rows = domain_app.dataset.repository.client.fetchall(
                "SELECT id, timestamp, downloads_count, api_calls_count, snapshot, COALESCE(snapshot->>'title', snapshot->'metas'->>'title') AS title "
                "FROM dataset_versions WHERE dataset_id = %s ORDER BY timestamp DESC LIMIT 50",
                (str(dataset_id),),
            )
            snapshots = [
                {
                    "id": r["id"],
                    "timestamp": (r["timestamp"].isoformat() if r.get("timestamp") else None),
                    "downloads_count": r.get("downloads_count"),
                    "api_calls_count": r.get("api_calls_count"),
                    "page": d.get("page"),
                    "title": r.get("title"),
                    "data": r.get("snapshot"),
                }
                for r in list_rows
            ]

        return {
            "id": d["id"],
            "platform_id": d["platform_id"],
            "publisher": d.get("publisher"),
            "buid": d["buid"],
            "slug": d["slug"],
            "page": d.get("page"),
            "created": d["created"].isoformat() if d.get("created") else None,
            "modified": d["modified"].isoformat() if d.get("modified") else None,
            "published": d.get("published"),
            "restricted": d.get("restricted"),
            "deleted": d.get("deleted"),
            "has_description": d.get("has_description", None),
            "quality": {
                "has_description": d.get("has_description"),
                "is_slug_valid": d.get("is_slug_valid"),
                "evaluation_results": d.get("evaluation_results"),
            },
            "current_snapshot": current_snapshot,
            "snapshots": snapshots,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/versions")
async def get_dataset_versions(dataset_id: UUID, page: int = 1, page_size: int = 10, include_data: bool = False):
    """
    Liste paginée des versions (snapshots) d'un dataset.
    """
    try:
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size

        cnt_rows = domain_app.dataset.repository.client.fetchall(
            "SELECT COUNT(*) AS cnt FROM dataset_versions WHERE dataset_id = %s",
            (str(dataset_id),),
        )
        total = int(cnt_rows[0]["cnt"]) if cnt_rows else 0

        rows = domain_app.dataset.repository.client.fetchall(
            "SELECT id, timestamp, downloads_count, api_calls_count, snapshot, COALESCE(snapshot->>'title', snapshot->'metas'->>'title') AS title "
            "FROM dataset_versions WHERE dataset_id = %s ORDER BY timestamp DESC LIMIT %s OFFSET %s",
            (str(dataset_id), page_size, offset),
        )
        items = [
            {
                "id": r["id"],
                "timestamp": r["timestamp"].isoformat() if r.get("timestamp") else None,
                "downloads_count": r.get("downloads_count"),
                "api_calls_count": r.get("api_calls_count"),
                "page": None,
                "title": r.get("title"),
                "data": r.get("snapshot") if include_data else None,
            }
            for r in rows
        ]
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/publisher/{publisher_name}")
async def get_by_publisher(publisher_name: str):
    """
    Récupère la liste des datasets liés à un publisher précis.

    Équivalent de la commande CLI: `app dataset get publisher "<publisher>"`
    Mais retourne les données au format JSON au lieu de créer un fichier CSV.
    """
    try:
        query = """
        SELECT p.name, d.timestamp, d.buid, d.slug, d.page, d.publisher, d.created, d.modified, d.published, d.restricted, d.last_sync, d.deleted
        FROM datasets d
        JOIN platforms p ON p.id = d.platform_id
        WHERE d.publisher ILIKE %s
        ORDER BY timestamp DESC
        """

        pattern = f"%{publisher_name}%"

        datasets_raw = domain_app.dataset.repository.client.fetchall(query, (pattern,))

        datasets_list = [
            DatasetAPI(
                name=dataset["name"],
                timestamp=dataset["timestamp"],
                buid=dataset["buid"],
                slug=dataset["slug"],
                page=dataset["page"],
                publisher=dataset["publisher"],
                published=dataset["published"],
                restricted=dataset["restricted"],
                last_sync=dataset["last_sync"],
                created=dataset["created"],
                modified=dataset["modified"],
                deleted=dataset["deleted"],
            )
            for dataset in datasets_raw
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{dataset_id}/evaluate")
async def evaluate_dataset(dataset_id: UUID):
    """
    Déclenche une évaluation de qualité par LLM pour un dataset.
    """
    try:
        # Initialize service (OpenAI by default for now)
        evaluator = OpenAIEvaluator(model_name="gpt-4o-mini")
        service = QualityAssessmentService(evaluator=evaluator, uow=domain_app.uow)
        
        # Paths to reference docs (should be configurable or standard)
        dcat_path = "docs/quality/dcat_reference.md"
        charter_path = "docs/quality/charter_opendata.md"
        
        evaluation = service.evaluate_dataset(
            dataset_id=str(dataset_id),
            dcat_path=dcat_path,
            charter_path=charter_path,
            output="json"
        )
        
        from dataclasses import asdict
        return asdict(evaluation)
    except Exception as e:
        logger.error(f"Evaluation failed for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
