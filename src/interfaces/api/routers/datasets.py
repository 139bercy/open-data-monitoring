"""
Router pour les endpoints datasets (STUB)  
TODO: Implémenter les endpoints dataset
"""

from fastapi import APIRouter, HTTPException
from interfaces.api.schemas.datasets import DatasetCreateResponse, DatasetResponse, DatasetAPI
from settings import app as domain_app
from pprint import pprint
from application.handlers import find_platform_from_url, find_dataset_id_from_url, fetch_dataset, upsert_dataset
from exceptions import DatasetHasNotChanged, DatasetUnreachableError
from logger import logger

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
        SELECT d.*
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
                created=dataset["created"],
                modified=dataset["modified"],
            ) for dataset in datasets_raw
        ]
        return DatasetResponse(
            datasets=datasets_list,
            total_datasets=len(datasets_list)
        )
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
        SELECT p.name, d.timestamp, d.buid, d.slug, d.page, d.publisher, d.created, d.modified, d.published, d.restricted, d.last_sync
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
            ) for dataset in datasets_raw
        ]

        return DatasetResponse(
            datasets=datasets_list,
            total_datasets=len(datasets_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
