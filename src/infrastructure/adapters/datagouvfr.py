import datetime

import requests

from application.dtos.dataset import DatasetDTO
from domain.platform.ports import DatasetAdapter, PlatformAdapter
from exceptions import DatasetUnreachableError


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
        query = f"{url}/api/1/datasets/{dataset_id}/"
        response = requests.get(query)
        if response.status_code != 200:
            raise DatasetUnreachableError(
                f"DATAGOUVFR :: {response.status_code} for '{query}'"
            )
        return response.json()

    @staticmethod
    def find_dataset_id(url: str):
        if url.endswith("/"):
            return url.split("/")[-2]
        return url.split("/")[-1]

    @staticmethod
    def map(
            id,
            slug,
            page,
            created_at,
            last_update,
            contact_points,
            archived,
            metrics,
            *args,
            **kwargs,
    ):
        publisher = next(
            (
                item.get("name")
                for item in contact_points
                if item["role"] == "publisher"
            ),
            None,
        )
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            page=page,
            publisher=publisher,
            created=created_at,
            modified=last_update,
            published=True if archived is None else False,
            restricted=False if archived is None else True,
            downloads_count=metrics.get("resources_downloads", None),
            api_calls_count=None,
        )
        return dataset
