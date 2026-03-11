"""Port (interface) for LLM-based metadata evaluation."""

from abc import ABC, abstractmethod

from domain.datasets.aggregate import Dataset
from domain.quality.evaluation import MetadataEvaluation


class LLMEvaluator(ABC):
    """Abstract interface for LLM-based metadata quality evaluation."""

    @abstractmethod
    def evaluate_metadata(
        self, dataset: Dataset, dcat_reference: str, charter: str, output: str, prompt_type: str = "standard"
    ) -> MetadataEvaluation:
        """
        Evaluate dataset metadata quality using LLM.

        Args:
            dataset: Dataset to evaluate
            dcat_reference: DCAT reference documentation (Markdown)
            charter: Open Data charter documentation (Markdown)
            output: Choose output format between text or json

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        raise NotImplementedError


class MetadataMapper(ABC):
    """Abstract interface for mapping platform-specific raw metadata to a standard LLM context."""

    @abstractmethod
    def map_to_llm_context(self, dataset: Dataset, raw_data: dict) -> dict:
        """
        Extract relevant metadata from raw platform data for LLM processing.

        Args:
            dataset: The dataset aggregate
            raw_data: Raw metadata from the platform

        Returns:
            Standardized dictionary for the LLM prompt
        """
        raise NotImplementedError
