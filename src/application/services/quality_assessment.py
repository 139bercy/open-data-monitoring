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
        Orchestrate the quality evaluation of a dataset.
        """
        with self.uow:
            dataset_uuid = self._resolve_dataset_uuid(dataset_id)
            dataset_obj = self.uow.datasets.get(dataset_uuid)
            if not dataset_obj:
                raise ValueError(f"Dataset not found: {dataset_uuid}")

            dcat_ref, charter = self._load_references(dcat_path, charter_path)
            llm_context = self._get_llm_context(dataset_obj)

            evaluation = self._run_llm_evaluation(
                llm_context, dcat_ref, charter, output, prompt_type
            )

            return self._persist_results(dataset_obj, evaluation)

    def _load_references(self, dcat_path: str, charter_path: str) -> tuple[str, str]:
        return self._load_markdown(dcat_path), self._load_markdown(charter_path)

    def _get_llm_context(self, dataset_obj: any) -> dict:
        raw_dataset = dataset_obj.raw
        if dataset_obj.versions:
            raw_dataset = dataset_obj.versions[-1].snapshot
        return self._prepare_llm_context(dataset_obj, raw_dataset)

    def _run_llm_evaluation(self, context, dcat, charter, out, p_type) -> MetadataEvaluation:
        return self.evaluator.evaluate_metadata(
            dataset=context, dcat_reference=dcat, charter=charter, output=out, prompt_type=p_type
        )

    def _persist_results(self, dataset: any, evaluation: MetadataEvaluation) -> MetadataEvaluation:
        evaluation.dataset_id = dataset.id
        evaluation.dataset_slug = str(dataset.slug)

        from dataclasses import asdict
        eval_data = asdict(evaluation)
        eval_data["dataset_id"] = str(eval_data["dataset_id"])
        eval_data["evaluated_at"] = eval_data["evaluated_at"].isoformat()

        previous_raw = dataset.versions[-1].snapshot if dataset.versions else None
        dataset.add_quality(
            downloads_count=dataset.downloads_count,
            api_calls_count=dataset.api_calls_count,
            has_description=dataset.has_description(),
            is_slug_valid=dataset.slug.is_valid(),
            evaluation_results=eval_data,
            previous_raw=previous_raw,
        )

        self.uow.datasets.add(dataset)
        self.uow.commit()
        logger.info(f"Evaluation complete for {dataset.slug}: score={evaluation.overall_score:.1f}")
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


    def _load_markdown(self, path: str) -> str:
        """Load markdown file content."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Reference file not found: {path}")

        return file_path.read_text(encoding="utf-8")
