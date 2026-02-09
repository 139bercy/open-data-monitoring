import os

import requests

from application.dtos.dataset import DatasetDTO
from domain.datasets.exceptions import DatasetUnreachableError
from domain.datasets.value_objects import DatasetQuality
from domain.platform.ports import DatasetAdapter


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
        try:
            automation_data = automation.json()
            catalog_data = catalog.json()
            monitoring_data = monitoring.json()
            data = {
                **automation_data["results"][0],
                **catalog_data,
                **monitoring_data[0],
            }
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
        quality = DatasetQuality(
            downloads_count=kwargs.get("download_count", None),
            api_calls_count=kwargs.get("api_call_count", None),
            has_description=(True if metadata.get("default", {}).get("description", None) else False),
            is_slug_valid="_" not in dataset_id,
        )
        title = metadata.get("default", {}).get("title", dataset_id)
        if isinstance(title, dict):
            title = title.get("value", dataset_id)

        dataset = DatasetDTO(
            buid=uid,
            slug=dataset_id,
            title=title,
            page=f"https://data.economie.gouv.fr/explore/dataset/{dataset_id}/information/",
            publisher=metadata.get("default", {}).get("publisher", {}).get("value", None),
            created=created_at,
            modified=updated_at,
            published=is_published,
            restricted=is_restricted,
            downloads_count=kwargs.get("download_count", None),
            api_calls_count=kwargs.get("api_call_count", None),
            reuses_count=kwargs.get("reuse_count", None),
            popularity_score=kwargs.get("popularity_score", None),
            quality=quality,
        )
        return dataset
