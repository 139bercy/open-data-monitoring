from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.datasets.aggregate import Dataset
from domain.datasets.ports import AbstractDatasetRepository
from domain.datasets.value_objects import DatasetVersionParams
from domain.platform.aggregate import Platform
from infrastructure.factories.dataset import DatasetAdapterFactory
from domain.datasets.exceptions import DatasetUnreachableError
from logger import logger

@dataclass(frozen=True)
class SyncDatasetCommand:
    platform: Platform
    platform_dataset_id: str

@dataclass(frozen=True)
class SyncDatasetOutput:
    dataset_id: Optional[UUID]
    status: str
    message: str = ""

class SyncDatasetUseCase:
    def __init__(self, repository: AbstractDatasetRepository, uow):
        self.repository = repository
        self.uow = uow
        self.adapter_factory = DatasetAdapterFactory()

    def handle(self, command: SyncDatasetCommand) -> SyncDatasetOutput:
        """
        Main orchestration for dataset synchronization.
        """
        raw_data = self._fetch_raw_data(command.platform, command.platform_dataset_id)
        if isinstance(raw_data, SyncDatasetOutput):
            return raw_data

        instance = self._create_dataset_instance(command.platform, raw_data)
        if isinstance(instance, SyncDatasetOutput):
            return instance

        return self._persist_and_link(command.platform, instance)

    def _fetch_raw_data(self, platform: Platform, platform_dataset_id: str) -> dict | SyncDatasetOutput:
        adapter = self.adapter_factory.create(platform_type=platform.type)
        try:
            raw_data = adapter.fetch(platform.url, platform.key, platform_dataset_id)
            if not raw_data or raw_data.get("sync_status") == "failed":
                return SyncDatasetOutput(dataset_id=None, status="failed", message="Fetch failed")
            return raw_data
        except DatasetUnreachableError:
            return SyncDatasetOutput(dataset_id=None, status="failed", message="Unreachable")

    def _create_dataset_instance(self, platform: Platform, raw_data: dict) -> Dataset | SyncDatasetOutput:
        from domain.datasets.factory import DatasetFactory
        try:
            adapter = self.adapter_factory.create(platform_type=platform.type)
            instance = DatasetFactory.create_from_adapter(adapter=adapter, platform=platform, raw_data=raw_data)
            instance.prepare_for_persistence()
            return instance
        except Exception as e:
            return SyncDatasetOutput(dataset_id=None, status="failed", message=str(e))

    def _persist_and_link(self, platform: Platform, instance: Dataset) -> SyncDatasetOutput:
        with self.uow:
            existing = self.repository.get_by_buid(instance.buid)
            if existing:
                instance.merge_with_existing(existing)

            self.repository.add(dataset=instance)
            
            if not existing or existing.should_version(instance):
                self._add_version(instance)

            self.repository.update_dataset_sync_status(platform.id, instance.id, "success")
            self._link_datasets(instance)
            
            return SyncDatasetOutput(dataset_id=instance.id, status="success")

    def _add_version(self, instance: Dataset) -> None:
        params = DatasetVersionParams(
            dataset_id=instance.id,
            snapshot=instance.raw,
            checksum=instance.checksum,
            title=instance.title,
            downloads_count=instance.downloads_count,
            api_calls_count=instance.api_calls_count,
            views_count=instance.views_count,
            reuses_count=instance.reuses_count,
            followers_count=instance.followers_count,
            popularity_score=instance.popularity_score,
        )
        self.repository.add_version(params)

    def _link_datasets(self, dataset: Dataset) -> None:
        """
        Reconcile datasets between ODS (economie.gouv.fr) and DataGouv.
        """
        linked_slug = dataset.extract_external_link_slug() or str(dataset.slug)
        linked_id = self.repository.get_id_by_slug_globally(slug=linked_slug, exclude_id=dataset.id)
        
        if not linked_id:
            return

        linked_dataset = self.repository.get(linked_id, include_versions=False)
        if not linked_dataset:
            return

        is_ods = lambda d: str(d.page).startswith("https://data.economie.gouv.fr")
        is_dg = lambda d: "data.gouv.fr" in str(d.page)

        # Establish link if it's an ODS <-> DG pair
        if (is_ods(dataset) and is_dg(linked_dataset)) or (is_dg(dataset) and is_ods(linked_dataset)):
            self._establish_bidirectional_link(dataset, linked_dataset)

    def _establish_bidirectional_link(self, d1: Dataset, d2: Dataset) -> None:
        d1.linked_dataset_id = d2.id
        d2.linked_dataset_id = d1.id
        self.repository.update_linking(d1)
        self.repository.update_linking(d2)
        logger.info(f"Link established (Bidirectional): {d1.slug} <-> {d2.slug}")
