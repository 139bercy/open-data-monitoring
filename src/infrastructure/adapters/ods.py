import datetime
import os

import requests

from domain.platform.ports import PlatformAdapter


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


