from __future__ import annotations

from dataclasses import dataclass

from domain.datasets.ports import AbstractDatasetRepository
from domain.platform.aggregate import Platform
from logger import logger


@dataclass(frozen=True)
class CheckDeletedDatasetsCommand:
    platform: Platform
    datasets: list[dict]


@dataclass(frozen=True)
class CheckDeletedDatasetsOutput:
    status: str
    deleted_count: int


class CheckDeletedDatasetsUseCase:
    def __init__(self, uow):
        self.uow = uow

    @property
    def repository(self) -> AbstractDatasetRepository:
        return self.uow.datasets

    def handle(self, command: CheckDeletedDatasetsCommand) -> CheckDeletedDatasetsOutput:
        """
        Detect datasets that were removed from the source platform and mark them as deleted.
        """
        with self.uow:
            in_base = self.repository.get_buids(platform_id=command.platform.id)
            # Support multiple ID keys from different platforms
            in_crawler = [d.get("uid") or d.get("id") or d.get("dataset_id") for d in command.datasets]
            deleted_buids = set(in_base) - set(in_crawler)

            for buid in deleted_buids:
                dataset = self.repository.get_by_buid(dataset_buid=buid)
                if dataset and not dataset.is_deleted:
                    dataset.mark_as_deleted()
                    self.repository.update_dataset_state(dataset)
                    logger.info(f"{command.platform.type.upper()} - Dataset '{dataset.slug}' deleted")

            return CheckDeletedDatasetsOutput(status="success", deleted_count=len(deleted_buids))
