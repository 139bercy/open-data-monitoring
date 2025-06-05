from domain.platform.ports import AbstractDatasetAdapterFactory, DatasetAdapter
from infrastructure.adapters.datagouvfr import DatagouvDatasetAdapter
from infrastructure.adapters.in_memory import InMemoryDatasetAdapter
from infrastructure.adapters.ods import OpendatasoftDatasetAdapter


class DatasetAdapterFactory(AbstractDatasetAdapterFactory):
    def create(self, platform_type: str) -> DatasetAdapter:
        if platform_type == "opendatasoft":
            return OpendatasoftDatasetAdapter()
        elif platform_type == "datagouvfr":
            return DatagouvDatasetAdapter()
        elif platform_type == "test":
            return InMemoryDatasetAdapter()
        else:
            raise ValueError("Unsupported platform type")
