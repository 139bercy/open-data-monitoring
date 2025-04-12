from infrastructure.adapters.ods import (
    OpendatasoftAdapter,
)
from infrastructure.adapters.in_memory import InMemoryAdapter
from infrastructure.adapters.datagouvfr import DataGouvFrAdapter


class AdapterFactory:
    @staticmethod
    def create(platform_type: str, url: str, key: str, slug: str):
        if platform_type == "opendatasoft":
            return OpendatasoftAdapter(url=url, key=key, slug=slug)
        elif platform_type == "datagouvfr":
            return DataGouvFrAdapter(url=url, key=key, slug=slug)
        elif platform_type == "test":
            return InMemoryAdapter(url=url, key=key, slug=slug)
        else:
            raise ValueError("Unsupported platform type")
