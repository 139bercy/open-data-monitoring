import os
from datetime import datetime

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
    def _parse_modified_date(modified_str, fallback):
        """Parse modified date which can be either 'YYYY-MM-DD' or an ISO timestamp."""
        if not modified_str:
            return fallback

        # If it's already a datetime object, return it
        if isinstance(modified_str, datetime):
            return modified_str

        # If it's a string, try to parse it
        if isinstance(modified_str, str):
            # Try date-only format first (from metadata.default.modified)
            try:
                return datetime.strptime(modified_str, "%Y-%m-%d")
            except ValueError:
                # Fallback to ISO format
                try:
                    return datetime.fromisoformat(modified_str.replace("Z", "+00:00"))
                except ValueError:
                    return fallback

        return fallback

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

        # Get modified date from metadata.default.modified (YYYY-MM-DD format) or fall back to updated_at
        modified_raw = (
            metadata.get("default", {}).get("modified", {}).get("value")
            if isinstance(metadata.get("default", {}).get("modified"), dict)
            else kwargs.get("modified")
        )
        modified = OpendatasoftDatasetAdapter._parse_modified_date(modified_raw, updated_at)

        dataset = DatasetDTO(
            buid=uid,
            slug=dataset_id,
            title=title,
            page=f"https://data.economie.gouv.fr/explore/dataset/{dataset_id}/information/",
            publisher=metadata.get("default", {}).get("publisher", {}).get("value", None),
            created=created_at,
            modified=modified,
            published=is_published,
            restricted=is_restricted,
            downloads_count=kwargs.get("download_count", None),
            api_calls_count=kwargs.get("api_call_count", None),
            reuses_count=kwargs.get("reuse_count", None),
            popularity_score=kwargs.get("popularity_score", None),
            quality=quality,
        )
        return dataset
