from domain.platform.ports import AbstractDatasetAdapterFactory, DatasetAdapter
from infrastructure.adapters.datasets.datagouvfr import DatagouvDatasetAdapter
from infrastructure.adapters.datasets.in_memory import InMemoryDatasetAdapter
from infrastructure.adapters.datasets.ods import OpendatasoftDatasetAdapter


class DatasetAdapterFactory(AbstractDatasetAdapterFactory):
    def create(self, platform_type: str) -> DatasetAdapter:
        if platform_type == "opendatasoft":
            return OpendatasoftDatasetAdapter()
        elif platform_type in ("datagouv", "datagouvfr"):
            return DatagouvDatasetAdapter()
        elif platform_type == "test":
            return InMemoryDatasetAdapter()
        else:
            raise ValueError(f"Unsupported platform type: {platform_type}")
