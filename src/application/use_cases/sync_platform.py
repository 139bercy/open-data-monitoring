from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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
    def __init__(self, repository: PlatformRepository, dataset_repository: AbstractDatasetRepository, uow):
        self.repository = repository
        self.dataset_repository = dataset_repository
        self.uow = uow
        self.factory = PlatformAdapterFactory()

    def handle(self, command: SyncPlatformCommand) -> SyncPlatformOutput:
        """
        Main orchestration for platform metadata sync.
        """
        with self.uow:
            platform = self.repository.get(platform_id=command.platform_id)
            if not platform:
                return SyncPlatformOutput(status="failed", message="Not found")

            return self._execute_sync(platform)

    def _execute_sync(self, platform: Platform) -> SyncPlatformOutput:
        adapter = self.factory.create(
            platform_type=platform.type,
            url=platform.url,
            key=platform.key,
            slug=platform.slug,
        )
        try:
            payload = adapter.fetch()
            platform.sync(**payload)
            self.repository.save_sync(platform_id=platform.id, payload=payload)

            # Refresh analytics views after meta sync
            self.dataset_repository.refresh_materialized_views()

            return SyncPlatformOutput(status="success", message="Completed")
        except Exception as e:
            return SyncPlatformOutput(status="failed", message=str(e))
