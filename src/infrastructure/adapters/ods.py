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

    def fetch(self, url: str, key: str, dataset_id: str):
        key = os.environ[key]
        response = requests.get(
            f"{url}/api/automation/v1.0/datasets/",
            headers={"Authorization": f"Apikey {key}"},
            params={"dataset_id": dataset_id},
        )
        data = response.json()
        return data["results"][0]

    @staticmethod
    def map(
        uid, dataset_id, metadata, created_at, updated_at, is_published, is_restricted, *args, **kwargs
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
            restricted=is_restricted
        )
        return dataset
