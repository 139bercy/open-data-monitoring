import datetime
import json
import os
from pprint import pprint

import requests

from application.dtos.dataset import DatasetDTO
from domain.platform.ports import DatasetAdapter, PlatformAdapter
from exceptions import DatasetUnreachableError


def load_json_by_id(data, dataset_id) -> dict:
    """Charge un fichier JSON et crée un dictionnaire indexé par une clé"""
    return next((item for item in data if item["dataset_id"] == dataset_id), None)



class OpendatasoftAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = os.environ[key]
        self.slug = slug

    def fetch(self) -> dict:
        response = requests.get(
            f"{self.url}/api/v2/catalog/datasets",
            headers={"Authorization": f"Apikey {self.key}"},
            params={"offset+limit": 1000},
        )
        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "success" if response.status_code == 200 else "failed",
            "datasets_count": response.json()["total_count"],
        }
        return sync_data


class OpendatasoftDatasetAdapter(DatasetAdapter):
    @staticmethod
    def find_dataset_id(url: str):
        if url.endswith("/"):
            return url.split("/")[-2]
        return url.split("/")[-1]

    def fetch(self, url: str, key: str, dataset_id: str):
        key = os.environ[key]
        automation = requests.get(
            f"{url}/api/automation/v1.0/datasets/",
            headers={"Authorization": f"Apikey {key}"},
            params={"dataset_id": dataset_id},
        )
        catalog = requests.get(
            f"{url}/api/explore/v2.1/catalog/datasets/{dataset_id}/",
            headers={"Authorization": f"Apikey {key}"},
        )
        monitoring = requests.get(
            f"{url}/api/explore/v2.1/monitoring/datasets/ods-datasets-monitoring/exports/json/?where=dataset_id: '{dataset_id}'",
            headers={"Authorization": f"Apikey {key}"},
        )
        pprint(monitoring.json())
        # https://data.economie.gouv.fr/api/explore/v2.1/monitoring/datasets/ods-api-monitoring/exports/json/?where=dataset_id:'prix-des-carburants-en-france-flux-instantane-v2'
        try:
            automation_data = automation.json()
            catalog_data = catalog.json()
            monitoring_data = monitoring.json()
            # monitoring_data = load_json_by_id(monitoring.json(), dataset_id)
            data = {**automation_data["results"][0], **catalog_data, **monitoring_data[0]
                    }
            with open("zzz.json", "w") as file:
                json.dump(data, file, indent=2)
            return data
        except IndexError:
            raise DatasetUnreachableError()

    @staticmethod
    def map(
        uid,
        dataset_id,
        metadata,
        created_at,
        updated_at,
        is_published,
        is_restricted,
        *args,
        **kwargs,
    ) -> DatasetDTO:
        dataset = DatasetDTO(
            buid=uid,
            slug=dataset_id,
            page=f"https://data.economie.gouv.fr/explore/dataset/{dataset_id}/information/",
            publisher=metadata.get("default", {})
            .get("publisher", {})
            .get("value", None),
            created=created_at,
            modified=updated_at,
            published=is_published,
            restricted=is_restricted,
        )
        return dataset
