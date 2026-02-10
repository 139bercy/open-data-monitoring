from pathlib import Path
from uuid import UUID

from domain.quality.evaluation import MetadataEvaluation
from domain.quality.ports import LLMEvaluator
from domain.unit_of_work import UnitOfWork
from logger import logger


class QualityAssessmentService:
    """Service for assessing metadata quality using LLM."""

    def __init__(self, evaluator: LLMEvaluator, uow: UnitOfWork):
        """
        Initialize quality assessment service.

        Args:
            evaluator: LLM evaluator implementation
            uow: Unit of work for data access
        """
        self.evaluator = evaluator
        self.uow = uow

    def evaluate_dataset(
        self, dataset_id: str | UUID, dcat_path: str, charter_path: str, output: str
    ) -> MetadataEvaluation:
        """
        Evaluate metadata quality for a specific dataset using reference documents.
        Persists the evaluation results and updates the dataset's quality status.
        """
        # Ensure we work with UUID
        dataset_uuid = UUID(str(dataset_id)) if not isinstance(dataset_id, UUID) else dataset_id

        with self.uow:
            logger.info(f"Starting quality evaluation for dataset {dataset_uuid}")

            # Load reference documents
            dcat_reference = self._load_markdown(dcat_path)
            charter = self._load_markdown(charter_path)

            # Fetch dataset from repository
            dataset_obj = self.uow.datasets.get(dataset_uuid)
            if dataset_obj is None:
                raise ValueError(f"Dataset not found: {dataset_uuid}")

            # Determine the raw dataset for the LLM (prefer latest snapshot)
            raw_dataset = dataset_obj.versions[-1].snapshot if dataset_obj.versions else dataset_obj.raw

            # Execute evaluation
            evaluation = self.evaluator.evaluate_metadata(
                dataset=raw_dataset, dcat_reference=dcat_reference, charter=charter, output=output
            )

            evaluation.dataset_id = dataset_obj.id
            evaluation.dataset_slug = str(dataset_obj.slug)

            # Persist results
            from dataclasses import asdict

            evaluation_data = asdict(evaluation)
            evaluation_data["dataset_id"] = str(evaluation_data["dataset_id"])
            evaluation_data["evaluated_at"] = evaluation_data["evaluated_at"].isoformat()

            # Update quality metrics on the aggregate
            is_valid_slug = getattr(dataset_obj.quality, "is_slug_valid", True) if dataset_obj.quality else True
            dataset_obj.add_quality(
                downloads_count=dataset_obj.downloads_count,
                api_calls_count=dataset_obj.api_calls_count,
                has_description=bool(raw_dataset.get("description")),
                is_slug_valid=is_valid_slug,
                evaluation_results=evaluation_data,
            )

            self.uow.datasets.add(dataset_obj)
            self.uow.commit()

            logger.info(f"Evaluation complete for {dataset_obj.slug}: score={evaluation.overall_score:.1f}")

            return evaluation

    def _load_markdown(self, path: str) -> str:
        """Load markdown file content."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Reference file not found: {path}")

        return file_path.read_text(encoding="utf-8")
