from dataclasses import asdict
from typing import cast, Optional
from uuid import uuid4

from application.dtos.dataset import DatasetDTO
from domain.datasets.aggregate import Dataset
from domain.datasets.factory import DatasetFactory
from domain.datasets.ports import AbstractDatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import DatasetAdapter
from logger import logger


class DatasetMonitoring:
    def __init__(self, repository: AbstractDatasetRepository):
        self.repository = repository

    def add_dataset(self, platform: Optional[Platform], dataset: dict, adapter: DatasetAdapter) -> Optional[Dataset]:
        """
        Creates a Dataset aggregate. The adapter is now passed from the orchestration layer
        to avoid having the service depend on an infrastructure factory.
        """
        if platform is None:
            return None
        
        try:
            return DatasetFactory.create_from_adapter(
                adapter=adapter,
                platform=platform,
                raw_data=dataset
            )
        except Exception as e:
            logger.error(
                f"{platform.type.upper()} - Dataset {dataset.get('dataset_id')} - {dataset.get('slug')} has encountered an error: {e}"
            )
            return None
