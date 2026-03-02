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
        self,
        dataset_id: str | UUID,
        dcat_path: str,
        charter_path: str,
        output: str,
        prompt_type: str = "standard",
    ) -> MetadataEvaluation:
        """
        Evaluate metadata quality for a specific dataset using reference documents.
        Persists the evaluation results and updates the dataset's quality status.
        """
        with self.uow:
            dataset_uuid = self._resolve_dataset_uuid(dataset_id)
            logger.info(f"Starting quality evaluation for dataset {dataset_uuid}")

            dataset_obj = self.uow.datasets.get(dataset_uuid)
            if dataset_obj is None:
                raise ValueError(f"Dataset not found for UUID: {dataset_uuid}")

            dcat_reference = self._load_markdown(dcat_path)
            charter = self._load_markdown(charter_path)

            raw_dataset = dataset_obj.raw
            if dataset_obj.versions:
                raw_dataset = dataset_obj.versions[-1].snapshot

            llm_context = self._prepare_llm_context(dataset_obj, raw_dataset)

            # Execute evaluation
            evaluation = self.evaluator.evaluate_metadata(
                dataset=llm_context,
                dcat_reference=dcat_reference,
                charter=charter,
                output=output,
                prompt_type=prompt_type,
            )

            evaluation.dataset_id = dataset_obj.id
            evaluation.dataset_slug = str(dataset_obj.slug)

            # Persist results
            from dataclasses import asdict

            evaluation_data = asdict(evaluation)
            evaluation_data["dataset_id"] = str(evaluation_data["dataset_id"])
            evaluation_data["evaluated_at"] = evaluation_data["evaluated_at"].isoformat()

            # Update quality metrics on the aggregate
            dataset_obj.add_quality(
                downloads_count=dataset_obj.downloads_count,
                api_calls_count=dataset_obj.api_calls_count,
                has_description=self._check_has_description(raw_dataset),
                is_slug_valid=dataset_obj.slug.is_valid(),
                evaluation_results=evaluation_data,
            )

            self.uow.datasets.add(dataset_obj)
            self.uow.commit()

            logger.info(f"Evaluation complete for {dataset_obj.slug}: score={evaluation.overall_score:.1f}")

            return evaluation

    def _resolve_dataset_uuid(self, dataset_id: str | UUID) -> UUID:
        """Resolve dataset_id (might be a UUID or a slug) to a UUID."""
        if isinstance(dataset_id, UUID):
            return dataset_id

        try:
            return UUID(str(dataset_id))
        except ValueError:
            # Not a UUID, try to resolve as slug
            logger.info(f"Dataset ID '{dataset_id}' is not a UUID, searching by slug...")
            dataset_uuid = self.uow.datasets.get_id_by_slug_globally(str(dataset_id))
            if not dataset_uuid:
                raise ValueError(f"Dataset not found by UUID or slug: {dataset_id}")
            return dataset_uuid

    def _prepare_llm_context(self, dataset_obj: any, raw_dataset: dict) -> dict:
        """Focus the LLM on metadata only to reduce noise and context size."""
        llm_context = {
            "id": str(dataset_obj.id),
            "slug": str(dataset_obj.slug),
            "title": raw_dataset.get("title") or raw_dataset.get("dataset_id"),
            "publisher": raw_dataset.get("publisher"),
            "metas": {
                "default": raw_dataset.get("metas", {}).get("default", {}),
                "dcat": raw_dataset.get("metas", {}).get("dcat", {}),
            },
            "metadata": {
                "default": raw_dataset.get("metadata", {}).get("default", {}),
                "dcat": raw_dataset.get("metadata", {}).get("dcat", {}),
            },
        }
        # Remove empty dicts/None values to further clean up
        return {k: v for k, v in llm_context.items() if v and (not isinstance(v, dict) or any(v.values()))}

    def _check_has_description(self, raw_dataset: dict) -> bool:
        """Determine if description is missing (handling nested structures for ODS/DataGouv)."""

        def get_nested(d, *keys):
            for k in keys:
                if not isinstance(d, dict):
                    return None
                d = d.get(k)
            return d

        if raw_dataset.get("description"):
            return True
        if get_nested(raw_dataset, "metas", "default", "description"):
            return True
        if get_nested(raw_dataset, "metadata", "default", "description"):
            return True
        if get_nested(raw_dataset, "metadata", "default", "description", "value"):
            # Handle ODS V2 value-wrapped strings if present
            return True
        return False

    def _load_markdown(self, path: str) -> str:
        """Load markdown file content."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Reference file not found: {path}")

        return file_path.read_text(encoding="utf-8")
