import datetime
import os

import requests

from domain.platform.ports import PlatformAdapter, DatasetAdapter
from infrastructure.dtos.dataset import DatasetDTO


class OpendatasoftAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = os.environ[key]
        self.slug = slug

    def fetch_datasets(self) -> dict:
        response = requests.get(
            f"{self.url}/api/v2/catalog/datasets",
            headers={"Authorization": f"Apikey {self.key}"},
            params={"offset+limit": 1000},
        )
        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "Success" if response.status_code == 200 else "Failed",
            "datasets_count": response.json()["total_count"],
        }
        return sync_data


class OpendatasoftDatasetAdapter(DatasetAdapter):
    @staticmethod
    def map(uid, dataset_id, metadata, created_at, updated_at, *args, **kwargs):
        dataset = DatasetDTO(
            buid=uid,
            slug=dataset_id,
            page=f"https://data.economie.gouv.fr/explore/dataset/{dataset_id}/information/",
            publisher=metadata["default"]["publisher"]["value"],
            created=created_at,
            modified=updated_at
        )
        return dataset
