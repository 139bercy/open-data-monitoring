import datetime

from domain.platform.ports import PlatformAdapter


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
