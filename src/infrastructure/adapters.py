import datetime
import os

import requests

from domain.ports import PlatformAdapter


class InMemoryAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = key
        self.slug = slug

    def fetch_datasets(self) -> dict:
        return {
            "timestamp": datetime.datetime.now(),
            "status": "Success",
            "datasets_count": 10,
        }


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


class DataGouvFrAdapter(PlatformAdapter):
    def __init__(self, url: str, key: str, slug: str):
        self.url = url
        self.key = key
        self.slug = slug

    def fetch_datasets(self) -> dict:
        response = requests.get(
            f"{self.url}/api/1/organizations/{self.slug}/datasets/",
        )
        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "Success" if response.status_code == 200 else "Failed",
            "datasets_count": response.json()["total"],
        }
        return sync_data
