import requests

from application.dtos.dataset import DatasetDTO
from domain.datasets.exceptions import DatasetUnreachableError
from domain.datasets.value_objects import DatasetQuality
from domain.platform.ports import DatasetAdapter


class DatagouvDatasetAdapter(DatasetAdapter):
    def fetch(self, url, key, dataset_id):
        query = f"{url}/api/1/datasets/{dataset_id}/"
        response = requests.get(query)
        if response.status_code != 200:
            raise DatasetUnreachableError(f"DATAGOUVFR :: {response.status_code} for '{query}'")
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
            (item.get("name") for item in contact_points if item["role"] == "publisher"),
            None,
        )
        quality = DatasetQuality(
            downloads_count=metrics.get("resources_downloads", None),
            api_calls_count=None,
            has_description=True if kwargs.get("description", None) else False,
            is_slug_valid=True,
        )
        dataset = DatasetDTO(
            buid=id,
            slug=slug,
            title=kwargs.get("title", slug),
            page=page,
            publisher=publisher,
            created=created_at,
            modified=last_update,
            published=True if archived is None else False,
            restricted=False if archived is None else True,
            downloads_count=metrics.get("resources_downloads", None),
            api_calls_count=None,
            views_count=metrics.get("views", None),
            reuses_count=metrics.get("reuses", None),
            followers_count=metrics.get("followers", None),
            quality=quality,
        )
        return dataset
