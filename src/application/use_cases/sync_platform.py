from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from application.use_cases.check_deleted_datasets import (
    CheckDeletedDatasetsCommand,
    CheckDeletedDatasetsUseCase,
)
from domain.datasets.ports import AbstractDatasetRepository
from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository
from infrastructure.factories.platform import PlatformAdapterFactory


@dataclass(frozen=True)
class SyncPlatformCommand:
    platform_id: UUID


@dataclass(frozen=True)
class SyncPlatformOutput:
    status: str
    message: str = ""


class SyncPlatformUseCase:
    def __init__(self, uow):
        self.uow = uow
        self.factory = PlatformAdapterFactory()
        self.check_deleted_use_case = CheckDeletedDatasetsUseCase(uow)

    @property
    def repository(self) -> PlatformRepository:
        return self.uow.platforms

    @property
    def dataset_repository(self) -> AbstractDatasetRepository:
        return self.uow.datasets

    def handle(self, command: SyncPlatformCommand) -> SyncPlatformOutput:
        """
        Main orchestration for platform metadata sync.
        """
        with self.uow:
            platform = self.repository.get(platform_id=command.platform_id)
            if not platform:
                return SyncPlatformOutput(status="failed", message="Not found")

            output = self._execute_sync(platform)
            return output

    def _execute_sync(self, platform: Platform) -> SyncPlatformOutput:
        adapter = self.factory.create(
            platform_type=platform.type,
            url=platform.url,
            key=platform.key,
            slug=platform.slug,
        )
        try:
            payload = adapter.fetch()
            platform.sync(**{k: v for k, v in payload.items() if k != "datasets"})
            self.repository.save_sync(platform_id=platform.id, payload=payload)

            # Trigger deletion detection if dataset list is provided
            if "datasets" in payload:
                deletion_command = CheckDeletedDatasetsCommand(platform=platform, datasets=payload["datasets"])
                self.check_deleted_use_case.handle(deletion_command)

            # Refresh analytics views after meta sync
            self.dataset_repository.refresh_materialized_views()

            return SyncPlatformOutput(status="success", message="Completed")
        except Exception as e:
            return SyncPlatformOutput(status="failed", message=str(e))
