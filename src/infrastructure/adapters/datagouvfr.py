import datetime

import requests

from domain.platform.ports import PlatformAdapter, DatasetAdapter
from infrastructure.dtos.dataset import DatasetDTO


class DataGouvFrAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = key
        self.slug = slug

    def fetch(self) -> dict:
        response = requests.get(
            f"{self.url}/api/1/organizations/{self.slug}/datasets/",
        )
        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "Success" if response.status_code == 200 else "Failed",
            "datasets_count": response.json()["total"],
        }
        return sync_data


class DatagouvDatasetAdapter(DatasetAdapter):
    @staticmethod
    def map(id, slug, page, created_at, last_update, *args, **kwargs):
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            page=page,
            publisher="",
            created=created_at,
            modified=last_update
        )
        return dataset