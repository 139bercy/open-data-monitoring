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

    def evaluate_dataset(self, dataset_id: str, dcat_path: str, charter_path: str, output: str) -> MetadataEvaluation:
        """
        Evaluate metadata quality for a dataset.
        """
        with self.uow:
            logger.info(f"Starting quality evaluation for dataset {dataset_id}")

            # Load reference documents
            dcat_reference = self._load_markdown(dcat_path)
            charter = self._load_markdown(charter_path)

            # Fetch dataset from repository
            dataset_uuid = UUID(dataset_id) if isinstance(dataset_id, str) and "-" in dataset_id else dataset_id
            dataset_obj = self.uow.datasets.get(dataset_uuid)

            if dataset_obj is None:
                raise ValueError(f"Dataset not found: {dataset_id}")

            # Determine the raw dataset for the LLM
            # If the dataset has versions, use the latest snapshot
            if dataset_obj.versions:
                raw_dataset = dataset_obj.versions[-1].snapshot
            else:
                # Fallback (legacy/minimal)
                raw_dataset = dataset_obj.raw

            # Evaluate
            evaluation = self.evaluator.evaluate_metadata(
                dataset=raw_dataset, dcat_reference=dcat_reference, charter=charter, output=output
            )

            evaluation.dataset_id = dataset_obj.id
            evaluation.dataset_slug = str(dataset_obj.slug)

            # Persist results
            from dataclasses import asdict

            evaluation_data = asdict(evaluation)

            # Ensure evaluation_data is JSON serializable
            evaluation_data["dataset_id"] = str(evaluation_data["dataset_id"])
            evaluation_data["evaluated_at"] = evaluation_data["evaluated_at"].isoformat()

            # Add or update quality
            dataset_obj.add_quality(
                downloads_count=dataset_obj.quality.downloads_count if dataset_obj.quality else 0,
                api_calls_count=dataset_obj.quality.api_calls_count if dataset_obj.quality else 0,
                has_description=dataset_obj.quality.has_description if dataset_obj.quality else False,
                is_slug_valid=dataset_obj.quality.is_slug_valid if dataset_obj.quality else True,
                evaluation_results=evaluation_data,
            )

            self.uow.datasets.add(dataset_obj)
            self.uow.commit()

            logger.info(
                f"Evaluation complete and saved for {dataset_obj.slug}: "
                f"score={evaluation.overall_score:.1f}, "
                f"suggestions={len(evaluation.suggestions)}"
            )

            return evaluation

    def _load_markdown(self, path: str) -> str:
        """Load markdown file content."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Reference file not found: {path}")

        return file_path.read_text(encoding="utf-8")
