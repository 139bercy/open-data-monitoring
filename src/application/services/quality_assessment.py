"""Quality assessment service for metadata evaluation."""
import os

from pathlib import Path
from typing import Optional
from uuid import UUID
import requests

from domain.datasets.aggregate import Dataset
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

    def evaluate_dataset(self, dataset_id: str, dcat_path: str, charter_path: str) -> MetadataEvaluation:
        """
        Evaluate metadata quality for a dataset.

        Args:
            dataset_id: ID of dataset to evaluate
            dcat_path: Path to DCAT reference markdown file
            charter_path: Path to charter markdown file

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        logger.info(f"Starting quality evaluation for dataset {dataset_id}")

        # Load reference documents
        dcat_reference = self._load_markdown(dcat_path)
        charter = self._load_markdown(charter_path)

        # platform = self.uow.platforms.get_by_domain("data.economie.gouv.fr")
        # dataset_uuid = self.uow.datasets.get_id_by_slug(platform_id=platform.id, slug=dataset_id)
        # dataset = self.uow.datasets.get(dataset_uuid)
        # dataset.versions = [dataset.versions[-1]]

        response = requests.get(
            f"https://{os.environ.get("ODS_DOMAIN")}/api/explore/v2.1/catalog/datasets/{dataset_id}/",
            headers={"Authorization": f"Apikey {os.environ.get("DATA_ECO_API_KEY")}"},
        )
        dataset = response.json()

        # Evaluate
        evaluation = self.evaluator.evaluate_metadata(dataset=dataset, dcat_reference=dcat_reference, charter=charter)

        logger.info(
            f"Evaluation complete for {dataset.get("dataset_id")}: "
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
