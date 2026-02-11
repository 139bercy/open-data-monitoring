from __future__ import annotations

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

            # Determine the raw dataset for the LLM (prefer latest merged snapshot)
            raw_dataset = dataset_obj.raw
            if dataset_obj.versions:
                raw_dataset = dataset_obj.versions[-1].snapshot

            # Focus the LLM on metadata only to reduce noise (especially for ODS which includes fields, security, etc.)
            # We extract key blocks: metas, metadata, and root identifiers
            llm_context = {
                "title": raw_dataset.get("title") or raw_dataset.get("dataset_id"),
                "publisher": raw_dataset.get("publisher"),
                "metas": raw_dataset.get("metas"),
                "metadata": raw_dataset.get("metadata"),
            }
            # Remove None values to further clean up
            llm_context = {k: v for k, v in llm_context.items() if v is not None}

            # Execute evaluation
            evaluation = self.evaluator.evaluate_metadata(
                dataset=llm_context, dcat_reference=dcat_reference, charter=charter, output=output
            )

            evaluation.dataset_id = dataset_obj.id
            evaluation.dataset_slug = str(dataset_obj.slug)

            # Persist results
            from dataclasses import asdict

            evaluation_data = asdict(evaluation)
            evaluation_data["dataset_id"] = str(evaluation_data["dataset_id"])
            evaluation_data["evaluated_at"] = evaluation_data["evaluated_at"].isoformat()

            # Null-safe deep check helper
            def get_nested(d, *keys):
                for k in keys:
                    if not isinstance(d, dict):
                        return None
                    d = d.get(k)
                return d

            # Determine if description is missing (handling nested structures for ODS/DataGouv)
            has_desc = False
            if raw_dataset.get("description"):
                has_desc = True
            elif get_nested(raw_dataset, "metas", "default", "description"):
                has_desc = True
            elif get_nested(raw_dataset, "metadata", "default", "description"):
                has_desc = True
            elif get_nested(raw_dataset, "metadata", "default", "description", "value"):
                # Handle ODS V2 value-wrapped strings if present
                has_desc = True

            # Update quality metrics on the aggregate
            dataset_obj.add_quality(
                downloads_count=dataset_obj.downloads_count,
                api_calls_count=dataset_obj.api_calls_count,
                has_description=has_desc,
                is_slug_valid=dataset_obj.slug.is_valid(),
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
