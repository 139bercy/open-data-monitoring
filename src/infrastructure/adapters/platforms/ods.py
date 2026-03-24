import datetime
import os

import requests

from domain.platform.ports import PlatformAdapter


class OpendatasoftPlatformAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = os.environ[key]
        self.slug = slug

    def fetch(self) -> dict:
        datasets = []
        offset = 0
        limit = 100
        total_count = 0

        while True:
            response = requests.get(
                f"{self.url}/api/v2/catalog/datasets",
                headers={"Authorization": f"Apikey {self.key}"},
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            data = response.json()

            total_count = data.get("total_count", total_count)

            # ODS v2 returns datasets in a 'datasets' list, each containing a 'dataset' object
            batch = [
                {"uid": d["dataset"]["dataset_uid"], "dataset_id": d["dataset"]["dataset_id"]}
                for d in data.get("datasets", [])
                if "dataset" in d
            ]
            datasets.extend(batch)

            if len(datasets) >= total_count or not batch:
                break

            offset += limit

        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "success",
            "datasets_count": total_count,
            "datasets": datasets,
        }
        return sync_data
