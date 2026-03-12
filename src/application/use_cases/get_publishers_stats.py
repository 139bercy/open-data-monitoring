from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GetPublishersStatsCommand:
    pass


@dataclass(frozen=True)
class GetPublishersStatsOutput:
    stats: list[dict[str, Any]]


class GetPublishersStatsUseCase:
    def __init__(self, uow):
        self.uow = uow

    def handle(self, command: GetPublishersStatsCommand | None = None) -> GetPublishersStatsOutput:
        """
        Retrieve publisher statistics (dataset count per publisher).
        """
        if command is None:
            command = GetPublishersStatsCommand()
        with self.uow:
            stats = self.uow.datasets.get_publishers_stats()
            return GetPublishersStatsOutput(stats=stats)
