from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional
from uuid import UUID

from application.services.quality_assessment import QualityAssessmentService
from domain.quality.ports import LLMEvaluator, MetadataMapper
from logger import logger


@dataclass(frozen=True)
class EvaluateDatasetCommand:
    dataset_id: UUID
    dcat_path: str = "docs/quality/dcat_reference.md"
    charter_path: str = "docs/quality/charter_opendata.md"


@dataclass(frozen=True)
class EvaluateDatasetOutput:
    status: str
    evaluation: Optional[dict] = None
    error: Optional[str] = None


class EvaluateDatasetUseCase:
    def __init__(self, uow, evaluator: LLMEvaluator, mappers: dict[str, MetadataMapper] | None = None):
        self.uow = uow
        self.evaluator = evaluator
        self.mappers = mappers

    def handle(self, command: EvaluateDatasetCommand) -> EvaluateDatasetOutput:
        """
        Main orchestration for dataset evaluation.
        """
        try:
            results = self._perform_evaluation(command)
            return EvaluateDatasetOutput(status="success", evaluation=asdict(results))
        except Exception as e:
            logger.error(f"Evaluation failed for {command.dataset_id}: {e}")
            return EvaluateDatasetOutput(status="failed", error=str(e))

    def _perform_evaluation(self, command: EvaluateDatasetCommand):
        service = QualityAssessmentService(evaluator=self.evaluator, uow=self.uow, mappers=self.mappers)
        return service.evaluate_dataset(
            dataset_id=str(command.dataset_id),
            dcat_path=command.dcat_path,
            charter_path=command.charter_path,
            output="json",
        )
