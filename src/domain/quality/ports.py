"""Port (interface) for LLM-based metadata evaluation."""
from abc import ABC, abstractmethod

from domain.datasets.aggregate import Dataset
from domain.quality.evaluation import MetadataEvaluation


class LLMEvaluator(ABC):
    """Abstract interface for LLM-based metadata quality evaluation."""

    @abstractmethod
    def evaluate_metadata(self, dataset: Dataset, dcat_reference: str, charter: str) -> MetadataEvaluation:
        """
        Evaluate dataset metadata quality using LLM.

        Args:
            dataset: Dataset to evaluate
            dcat_reference: DCAT reference documentation (Markdown)
            charter: Open Data charter documentation (Markdown)

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        raise NotImplementedError
