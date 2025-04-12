import datetime
import os

import requests

from domain.ports import PlatformAdapter


class InMemoryAdapter(PlatformAdapter):
    def __init__(self, base_url: str, api_key: str, name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.name = name

    def fetch_datasets(self) -> dict:
        return {
            "timestamp": datetime.datetime.now(),
            "status": "Success",
            "datasets_count": 10,
        }


class OpendatasoftAdapter(PlatformAdapter):
    def __init__(self, base_url: str, api_key: str, slug: str):
        self.base_url = base_url
        self.api_key = os.environ[api_key]
        self.slug = slug

    def fetch_datasets(self) -> dict:
        response = requests.get(
            f"{self.base_url}/api/v2/catalog/datasets",
            headers={"Authorization": f"Apikey {self.api_key}"},
            params={"offset+limit": 1000},
        )
        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "Success" if response.status_code == 200 else "Failed",
            "datasets_count": response.json()["total_count"],
        }
        return sync_data


class DataGouvFrAdapter(PlatformAdapter):
    def __init__(self, base_url: str, api_key: str, slug: str):
        self.base_url = base_url
        self.api_key = api_key
        self.slug = slug

    def fetch_datasets(self) -> dict:
        response = requests.get(
            f"{self.base_url}/api/1/organizations/{self.slug}/datasets/",
        )
        sync_data = {
            "timestamp": datetime.datetime.now(),
            "status": "Success" if response.status_code == 200 else "Failed",
            "datasets_count": response.json()["total"],
        }
        return sync_data
