"""Gemini-based implementation of LLM metadata evaluator."""

import json
import os
from datetime import datetime
from typing import Optional

from google import genai
from pydantic import ValidationError

from domain.datasets.aggregate import Dataset
from domain.quality.evaluation import (CriterionScore, MetadataEvaluation,
                                       Suggestion)
from domain.quality.ports import LLMEvaluator
from infrastructure.llm.models import EvaluationResponse
from infrastructure.llm.prompts import build_system_prompt, build_user_prompt
from logger import logger


class GeminiEvaluator(LLMEvaluator):
    """Gemini-based metadata quality evaluator."""

    client = genai.Client()

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro"):
        """
        Initialize Gemini evaluator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name

    def evaluate_metadata(self, dataset: Dataset, dcat_reference: str, charter: str) -> MetadataEvaluation:
        """
        Evaluate dataset metadata using Gemini.

        Args:
            dataset: Dataset to evaluate
            dcat_reference: DCAT reference (Markdown)
            charter: Open Data charter (Markdown)

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        logger.info(f"Evaluating metadata for dataset {dataset.id}")

        # Build prompts
        system_prompt = build_system_prompt(dcat_reference, charter)
        user_prompt = build_user_prompt(dataset)

        # Call Gemini
        try:
            response = self.client.models.generate_content(
                [system_prompt, user_prompt],
                generation_config=genai.GenerationConfig(
                    temperature=0.1, response_mime_type="application/json"  # Low temperature for consistent evaluation
                ),
            )

            # Parse response
            response_text = response.text
            logger.debug(f"Gemini response: {response_text}")

            # Validate with Pydantic
            evaluation_data = json.loads(response_text)
            validated = EvaluationResponse(**evaluation_data)

            # Convert to domain model
            return self._to_domain_model(dataset, validated)

        except ValidationError as e:
            logger.error(f"Failed to validate Gemini response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"LLM evaluation failed: {e}")

    def _to_domain_model(self, dataset: Dataset, response: EvaluationResponse) -> MetadataEvaluation:
        """Convert Pydantic response to domain model."""
        criteria_scores = {
            name: CriterionScore(
                criterion=name, category=score.category, score=score.score, weight=score.weight, issues=score.issues
            )
            for name, score in response.criteria_scores.items()
        }

        suggestions = [
            Suggestion(
                field=s.field,
                current_value=s.current_value,
                suggested_value=s.suggested_value,
                reason=s.reason,
                priority=s.priority,
            )
            for s in response.suggestions
        ]

        return MetadataEvaluation(
            dataset_id=dataset.id,
            dataset_slug=dataset.slug,
            evaluated_at=datetime.now(),
            overall_score=response.overall_score,
            criteria_scores=criteria_scores,
            suggestions=suggestions,
        )
