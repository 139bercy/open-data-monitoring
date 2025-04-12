import requests

from domain.ports import PlatformAdapter


class InMemoryAdapter(PlatformAdapter):
    def __init__(self, base_url: str, api_key: str, name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.name = name

    def fetch_datasets(self) -> int:
        return 10


class OpendatasoftAdapter(PlatformAdapter):
    def __init__(self, base_url: str, api_key: str, name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.name = name

    def fetch_datasets(self) -> int:
        response = requests.get(
            f"{self.base_url}/api/v2/catalog/datasets",
            headers={"Authorization": f"Apikey {self.api_key}"},
            params={"offset+limit": 1000},
        )
        return response.json()["total_count"]


class DataGouvFrAdapter(PlatformAdapter):
    def __init__(self, base_url: str, api_key: str, name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.name = name

    def fetch_datasets(self) -> int:
        response = requests.get(
            f"{self.base_url}/api/1/organizations/{self.name}/datasets/",
        )
        return response.json()["total"]
