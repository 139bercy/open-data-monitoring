"""
Utilitaire pour récupérer les données (datasets) des plateformes Open Data

Les données sont récupérées via les API de data.economie.gouv.fr

Les données ainsi récupérées sont fusionnées et servent à peupler la base de données.
"""

import json
import os

import requests
from dotenv import load_dotenv

from application.handlers import find_platform_from_url, upsert_dataset, create_platform
from exceptions import DatasetHasNotChanged, DatasetUnreachableError
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
        "params": {"limit": 1000},
        "filename": "data-eco-automation.json",
    },
    {
        "url": "https://data.economie.gouv.fr/api/explore/v2.1/monitoring/datasets/ods-datasets-monitoring/exports/json",
        "params": {
            "where": 'domain_id="opendatamef"',
            "order_by": "modified DESC",
            "limit": 1000,
        },
        "filename": "data-eco-monitoring.json",
    },
    {
        "url": "https://data.economie.gouv.fr/api/explore/v2.1/catalog/exports/json",
        "params": {"limit": 1000},
        "filename": "data-eco-catalog.json",
    },
]


# Fonctions utilitaires
def fetch_and_save_data(url: str, params: dict, filename: str) -> dict:
    """Récupère des données via API et les sauvegarde dans un fichier JSON"""
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Gestion des différents formats de réponse
        if isinstance(data, list):
            results = data  # Réponse directe sous forme de liste
        else:
            results = data.get("results", data)  # Réponse avec clé "results"

        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ {filename} - {len(results)} éléments sauvegardés")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erreur pour {filename}: {e}")
        return []


def load_json_by_id(filename: str, key: str = "dataset_id") -> dict:
    """Charge un fichier JSON et crée un dictionnaire indexé par une clé"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item[key]: item for item in data}
    except FileNotFoundError:
        logger.error(f"⚠️ Fichier {filename} non trouvé")
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
        data = fetch_and_save_data(
            endpoint["url"], endpoint["params"], endpoint["filename"]
        )
        datasets[endpoint["filename"]] = data

    automation = load_json_by_id("data-eco-automation.json", "dataset_id")
    monitoring = load_json_by_id("data-eco-monitoring.json", "dataset_id")
    catalog = load_json_by_id("data-eco-catalog.json", "dataset_id")

    merged_data = merge_datasets(automation, monitoring, catalog)
    logger.info(f"🔀 {len(merged_data)} datasets fusionnés")

    with open(
            os.path.join(OUTPUT_DIR, "data-eco.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    logger.info("💾 Fichier final data-eco.json sauvegardé")


def process_data_gouv():
    organization = os.environ["DATA_GOUV_ORGANIZATION"]
    url = f"http://www.data.gouv.fr/api/1/datasets/"
    params = {"organization": organization, "page_size": 1000}

    response = requests.get(url, params=params)
    # Robustifier la lecture du JSON retourné par data.gouv :
    # - certaines réponses contiennent une clé 'data' ; d'autres retournent
    #   directement une liste. On gère les deux cas et on journalise le
    #   contenu inattendu pour débogage.
    try:
        payload = response.json()
    except Exception as e:
        logger.error(f"❌ Impossible de décoder la réponse data.gouv : {e}")
        return

    if isinstance(payload, dict) and "data" in payload:
        # parfois 'data' peut être None; coerce en liste vide si nécessaire
        data = payload["data"] or []
    elif isinstance(payload, list):
        data = payload
    else:
        # Cas inattendu : sauvegarder la réponse brute pour analyse
        logger.error("⚠️ Réponse data.gouv inattendue, sauvegarde pour inspection")
        with open(os.path.join(OUTPUT_DIR, "data-gouv-raw.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Essayer d'extraire une liste depuis 'results' si présente,
        # avec fallback sur liste vide pour éviter TypeError en aval
        data = payload.get("results", []) if isinstance(payload, dict) else []

    with open(os.path.join(OUTPUT_DIR, "data-gouv.json"), "w", encoding="utf-8") as file:
        text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        file.write(text)

    with open(os.path.join(OUTPUT_DIR, "data-gouv.json"), "r") as file:
        data = json.load(file)
        for dataset in data:
            platform = find_platform_from_url(app=app, url=dataset["page"])
            try:
                upsert_dataset(app=app, platform=platform, dataset=dataset)
            except DatasetHasNotChanged as e:
                logger.error(f' - {dataset["dataset_id"]} - {e}')
            except DatasetUnreachableError:
                pass


def process_data_eco():
    merge_data_eco_datasets()
    with open(os.path.join(OUTPUT_DIR, "data-eco.json"), "r") as file:
        data = json.load(file)
        for dataset in data:
            # Chercher la platform existante par domaine. Si elle n'existe pas,
            # on la crée automatiquement avec des valeurs raisonnables afin
            # que l'ingestion puisse s'exécuter de façon idempotente.
            # Cela évite que l'ingestion soit silencieusement ignorée parce
            # que la plateforme n'a pas été enregistrée manuellement.
            platform = find_platform_from_url(app=app, url="https://data.economie.gouv.fr")
            try:
                if platform is None:
                    logger.info("Platform introuvable pour data.economie.gouv.fr — création automatique")
                    platform_payload = {
                        "name": "Data Economie",
                        "slug": "data-economie",
                        "organization_id": "opendatamef",
                        "type": "opendatasoft",
                        "url": "https://data.economie.gouv.fr",
                        "key": os.environ.get("DATA_ECO_API_KEY"),
                    }
                    try:
                        # create_platform gère l'insert via l'application (DDD)
                        create_platform(app=app, data=platform_payload)
                        # recharger la platform fraîchement créée
                        platform = find_platform_from_url(app=app, url=platform_payload["url"])
                    except Exception as ce:
                        logger.error(f"Erreur lors de la création automatique de la platform: {ce}")
                        # si on n'a pas pu créer la platform, on skip ce dataset
                        continue

                upsert_dataset(app=app, platform=platform, dataset=dataset)
            except Exception as e:
                logger.debug(f'OPENDATASOFT - {dataset.get("dataset_id", "?" )} - {e}')


if __name__ == "__main__":
    process_data_eco()
    process_data_gouv()
