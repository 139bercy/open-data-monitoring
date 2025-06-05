import datetime
import os

import requests

from application.dtos.dataset import DatasetDTO
from domain.platform.ports import DatasetAdapter, PlatformAdapter


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

    def fetch(self, url: str, key: str, dataset_id):
        key = os.environ[key]
        response = requests.get(
            f"{url}/api/explore/v2.1/catalog/datasets/{dataset_id}/",
            headers={"Authorization": f"Apikey {key}"},
        )
        data = response.json()
        dataset_uid = data.get("dataset_uid")
        response = requests.get(
            f"{url}/api/automation/v1.0/datasets/{dataset_uid}/",
            headers={"Authorization": f"Apikey {key}"},
        )
        return response.json()

    @staticmethod
    def map(uid, dataset_id, metadata, created_at, updated_at, *args, **kwargs):
        dataset = DatasetDTO(
            buid=uid,
            slug=dataset_id,
            page=f"https://data.economie.gouv.fr/explore/dataset/{dataset_id}/information/",
            publisher=metadata["default"]["publisher"]["value"],
            created=created_at,
            modified=updated_at,
        )
        return dataset
