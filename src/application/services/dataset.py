from __future__ import annotations

from uuid import UUID

from domain.datasets.aggregate import Dataset
from domain.datasets.factory import DatasetFactory
from domain.datasets.ports import AbstractDatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import DatasetAdapter
from logger import logger


class DatasetMonitoring:
    def __init__(self, repository: AbstractDatasetRepository):
        self.repository = repository

    def add_dataset(self, platform: Platform | None, dataset: dict, adapter: DatasetAdapter) -> Dataset | None:
        """
        Creates a Dataset aggregate. The adapter is now passed from the orchestration layer
        to avoid having the service depend on an infrastructure factory.
        """
        if platform is None:
            return None

        try:
            return DatasetFactory.create_from_adapter(adapter=adapter, platform=platform, raw_data=dataset)
        except Exception as e:
            logger.error(
                f"{platform.type.upper()} - Dataset {dataset.get('dataset_id')} - {dataset.get('slug')} has encountered an error: {e}"
            )
            return None

    def link_datasets(self, dataset_or_id: Dataset | str | UUID) -> None:
        """
        Reconcile datasets between ODS and DataGouv.
        If a Dataset object is passed, it uses it directly (preserving in-memory data like 'harvest').
        If an ID is passed, it fetches the dataset from the repository.
        """
        if isinstance(dataset_or_id, Dataset):
            dataset = dataset_or_id
        else:
            id_obj = dataset_or_id if isinstance(dataset_or_id, UUID) else UUID(dataset_or_id)
            dataset = self.repository.get(id_obj, include_versions=False)

        if not dataset:
            return

        linked_slug = dataset.extract_external_link_slug()

        # Loose search fallback: if no explicit link found in metadata,
        # try to find a dataset with the SAME slug on another platform
        if not linked_slug:
            linked_slug = str(dataset.slug)

        # Find the potential linked dataset by its slug
        # We exclude the current dataset ID to avoid linking to self
        linked_id = self.repository.get_id_by_slug_globally(slug=linked_slug, exclude_id=dataset.id)
        if not linked_id:
            return

        # Get the linked dataset to check its platform
        linked_dataset = self.repository.get(linked_id, include_versions=False)
        if not linked_dataset:
            return

        # Determine the direction of the link
        # We want BOTH datasets to be linked to each other

        page_str = str(dataset.page)
        linked_page_str = str(linked_dataset.page)

        # Case 1: Processing ODS dataset -> found DG link
        if page_str.startswith("https://data.economie.gouv.fr") and "data.gouv.fr" in linked_page_str:
            # Link ODS -> DG
            dataset.linked_dataset_id = linked_id
            self.repository.update_linking(dataset)

            # Link DG -> ODS
            linked_dataset.linked_dataset_id = dataset.id
            self.repository.update_linking(linked_dataset)

            logger.info(f"Link established (Bidirectional): {dataset.slug} <-> {linked_slug}")

        # Case 2: Processing DataGouv dataset -> found ODS link
        elif "data.gouv.fr" in page_str and linked_page_str.startswith("https://data.economie.gouv.fr"):
            # Link DG -> ODS
            dataset.linked_dataset_id = linked_id
            self.repository.update_linking(dataset)

            # Link ODS -> DG
            linked_dataset.linked_dataset_id = dataset.id
            self.repository.update_linking(linked_dataset)

            logger.info(f"Link established (Bidirectional): {dataset.slug} <-> {linked_dataset.slug}")
