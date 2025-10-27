import datetime

import requests

from domain.platform.ports import PlatformAdapter


class DataGouvPlatformAdapter(PlatformAdapter):
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
