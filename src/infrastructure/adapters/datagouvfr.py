import datetime
from pprint import pprint

import requests

from application.dtos.dataset import DatasetDTO
from domain.platform.ports import DatasetAdapter, PlatformAdapter


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
            "status": "success" if response.status_code == 200 else "failed",
            "datasets_count": response.json()["total"],
        }
        return sync_data


class DatagouvDatasetAdapter(DatasetAdapter):
    def fetch(self, url, key, dataset_id):
        response = requests.get(
            f"{url}/api/1/datasets/{dataset_id}/",
            headers={"Authorization": f"Apikey {key}"},
        )
        return response.json()

    @staticmethod
    def find_dataset_id(url: str):
        if url.endswith("/"):
            return url.split("/")[-2]
        return url.split("/")[-1]

    @staticmethod
    def map(id, slug, page, created_at, last_update, archived, *args, **kwargs):
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            page=page,
            publisher="",
            created=created_at,
            modified=last_update,
            published=True if archived is None else False,
            restricted=False if archived is None else True,
        )
        return dataset
