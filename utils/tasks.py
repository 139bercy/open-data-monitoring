"""
Utilitaire pour récupérer les données (datasets) des plateformes Open Data

Les données sont récupérées via les API de data.economie.gouv.fr

Les données ainsi récupérées sont fusionnées et servent à peupler la base de données.
"""

import json
import os
import time

import requests
from dotenv import load_dotenv

from application.handlers import find_platform_from_url
from application.use_cases.check_deleted_datasets import (
    CheckDeletedDatasetsCommand,
    CheckDeletedDatasetsUseCase,
)
from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase
from application.use_cases.sync_platform import SyncPlatformCommand, SyncPlatformUseCase
from domain.datasets.exceptions import DatasetUnreachableError
from logger import logger
from settings import BASE_DIR, ENV_PATH, app

load_dotenv(ENV_PATH)

API_KEY = os.environ["DATA_ECO_API_KEY"]
HEADERS = {"Authorization": f"Apikey {API_KEY}"}
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_ENDPOINTS = [
    {
        "url": "https://data.economie.gouv.fr/api/automation/v1.0/datasets",
        "params": {"limit": 5000},
        "filename": "data-eco-automation.json",
    },
    {
        "url": "https://data.economie.gouv.fr/api/explore/v2.1/monitoring/datasets/ods-datasets-monitoring/exports/json",
        "params": {
            "where": 'domain_id="opendatamef"',
            "order_by": "modified DESC",
            "limit": 5000,
        },
        "filename": "data-eco-monitoring.json",
    },
    {
        "url": "https://data.economie.gouv.fr/api/explore/v2.1/catalog/exports/json",
        "params": {"limit": 5000},
        "filename": "data-eco-catalog.json",
    },
]


# Fonctions utilitaires
def fetch_and_save_data(url: str, params: dict, filename: str) -> dict:
    """Récupère des données via API et les sauvegarde dans un fichier JSON"""
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Gestion des différents formats de réponse
        if isinstance(data, list):
            results = data  # Réponse directe sous forme de liste
        else:
            results = data.get("results", data)  # Réponse avec clé "results"

        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"📥 {filename} - {len(results)} items saved")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching {filename}: {e}")
        return []


def load_json_by_id(filename: str, key: str = "dataset_id") -> dict:
    """Charge un fichier JSON et crée un dictionnaire indexé par une clé"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
            return {item[key]: item for item in data}
    except FileNotFoundError:
        logger.warning(f"⚠️ File {filename} not found")
        return {}


def merge_datasets(*sources: dict) -> list:
    """Fusionne plusieurs sources de données par ID de dataset"""
    all_ids = set().union(*[source.keys() for source in sources])
    merged = []

    for dataset_id in all_ids:
        merged_data = {}
        for source in sources:
            if dataset_id in source:
                merged_data.update(source[dataset_id])

        if merged_data:
            merged.append(merged_data)
    return merged


def merge_data_eco_datasets():
    datasets = {}
    for endpoint in API_ENDPOINTS:
        data = fetch_and_save_data(endpoint["url"], endpoint["params"], endpoint["filename"])
        datasets[endpoint["filename"]] = data

    automation = load_json_by_id("data-eco-automation.json", "dataset_id")
    monitoring = load_json_by_id("data-eco-monitoring.json", "dataset_id")
    catalog = load_json_by_id("data-eco-catalog.json", "dataset_id")

    merged_data = merge_datasets(automation, monitoring, catalog)
    logger.info(f"🔀 {len(merged_data)} datasets merged")

    with open(os.path.join(OUTPUT_DIR, "data-eco.json"), "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    logger.info("💾 Final data-eco.json saved")


def get_data_gouv_datasets():
    organization = os.environ["DATA_GOUV_ORGANIZATION"]
    url = "http://www.data.gouv.fr/api/1/datasets/"
    params = {"organization": organization, "page_size": 1000}

    response = requests.get(url, params=params)
    with open(os.path.join(OUTPUT_DIR, "data-gouv.json"), "w") as file:
        data = response.json()["data"]
        text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        file.write(text)


def process_data_gouv():
    start_time = time.perf_counter()
    logger.info("🚀 Starting data.gouv.fr processing...")

    get_data_gouv_datasets()
    platform = find_platform_from_url(app=app, url="https://www.data.gouv.fr/")

    stats = {"success": 0, "failed": 0, "skipped": 0}

    with open(os.path.join(OUTPUT_DIR, "data-gouv.json")) as file:
        data = json.load(file)
        for dataset in data:
            try:
                SyncDatasetUseCase(uow=app.uow).handle(
                    SyncDatasetCommand(platform=platform, platform_dataset_id=dataset.get("id"), raw_data=dataset)
                )
                stats["success"] += 1
            except DatasetUnreachableError:
                stats["skipped"] += 1
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"❌ Failed to upsert {dataset.get('id', 'unknown')}: {e}")

    if platform:
        logger.info(f"🔄 Syncing platform metadata: {platform.slug}")
        SyncPlatformUseCase(uow=app.uow).handle(SyncPlatformCommand(platform_id=platform.id))

    with open(os.path.join(OUTPUT_DIR, "data-gouv.json")) as file:
        data = json.load(file)
        CheckDeletedDatasetsUseCase(uow=app.uow).handle(CheckDeletedDatasetsCommand(platform=platform, datasets=data))

    duration = time.perf_counter() - start_time
    logger.info(f"✅ data.gouv.fr completed in {duration:.2f}s")
    logger.info(f"📊 Stats: {stats['success']} successes, {stats['failed']} failures, {stats['skipped']} skipped")


def process_data_eco():
    start_time = time.perf_counter()
    logger.info("🚀 Starting data.economie.gouv.fr processing...")

    merge_data_eco_datasets()

    stats = {"success": 0, "failed": 0, "skipped": 0}

    with open(os.path.join(OUTPUT_DIR, "data-eco.json")) as file:
        data = json.load(file)
        platform = find_platform_from_url(app=app, url="https://data.economie.gouv.fr")
        if platform:
            logger.info(f"🔄 Syncing platform metadata: {platform.slug}")
            SyncPlatformUseCase(uow=app.uow).handle(SyncPlatformCommand(platform_id=platform.id))

        CheckDeletedDatasetsUseCase(uow=app.uow).handle(CheckDeletedDatasetsCommand(platform=platform, datasets=data))

        for dataset in data:
            try:
                if platform is None:
                    stats["skipped"] += 1
                    continue

                SyncDatasetUseCase(uow=app.uow).handle(
                    SyncDatasetCommand(
                        platform=platform, platform_dataset_id=dataset.get("dataset_id"), raw_data=dataset
                    )
                )
                stats["success"] += 1
            except DatasetUnreachableError:
                stats["skipped"] += 1
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"OPENDATASOFT - {dataset.get('dataset_id', 'unknown')} - {e}")

    duration = time.perf_counter() - start_time
    logger.info(f"✅ data.economie.gouv.fr completed in {duration:.2f}s")
    logger.info(f"📊 Stats: {stats['success']} successes, {stats['failed']} failures, {stats['skipped']} skipped")


if __name__ == "__main__":
    process_data_gouv()
    process_data_eco()
