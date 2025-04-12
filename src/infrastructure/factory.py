from infrastructure.adapters.ods import (
    OpendatasoftAdapter, OpendatasoftDatasetAdapter,
)
from infrastructure.adapters.in_memory import InMemoryAdapter, InMemoryDatasetAdapter
from infrastructure.adapters.datagouvfr import DataGouvFrAdapter, DatagouvDatasetAdapter


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


class DatasetAdapterFactory:
    @staticmethod
    def create(platform_type: str):
        if platform_type == "opendatasoft":
            return OpendatasoftDatasetAdapter()
        elif platform_type == "datagouvfr":
            return DatagouvDatasetAdapter()
        elif platform_type == "test":
            return InMemoryDatasetAdapter()
        else:
            raise ValueError("Unsupported platform type")

