import datetime

import requests

from domain.platform.ports import PlatformAdapter


class DataGouvPlatformAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = key
        self.slug = slug

    def fetch(self) -> dict:
        datasets = []
        url = f"{self.url}/api/1/organizations/{self.slug}/datasets/"
        total_count = 0

        while url:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            total_count = data.get("total", total_count)

            batch = [{"id": d["id"]} for d in data.get("data", [])]
            datasets.extend(batch)

            url = data.get("next_page")

        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "success",
            "datasets_count": total_count,
            "datasets": datasets,
        }
        return sync_data
