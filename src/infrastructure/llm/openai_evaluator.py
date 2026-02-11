"""OpenAI-based implementation of LLM metadata evaluator."""

import json
import os
from datetime import datetime

from openai import OpenAI
from pydantic import ValidationError

from domain.datasets.aggregate import Dataset
from domain.quality.evaluation import CriterionScore, MetadataEvaluation, Suggestion
from domain.quality.ports import LLMEvaluator
from infrastructure.llm.models import EvaluationResponse
from infrastructure.llm.prompts import build_system_prompt, build_user_prompt
from logger import logger


class OpenAIEvaluator(LLMEvaluator):
    """OpenAI-based metadata quality evaluator."""

    def __init__(self, api_key: str | None = None, model_name: str = "gpt-4o-mini"):
        """
        Initialize OpenAI evaluator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model_name: OpenAI model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set. Get your key at https://platform.openai.com/api-keys")

        self.client = OpenAI(api_key=self.api_key)
        self.model_name = model_name

    def evaluate_metadata(self, dataset: Dataset, dcat_reference: str, charter: str, output: str) -> MetadataEvaluation:
        """
        Evaluate dataset metadata using OpenAI.

        Args:
            dataset: Dataset to evaluate
            dcat_reference: DCAT reference (Markdown)
            charter: Open Data charter (Markdown)
            output: Output format (text or json)

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        logger.info(f"Evaluating metadata with OpenAI model {self.model_name}")

        # Build prompts
        try:
            system_prompt = build_system_prompt(dcat_reference, charter, output)
            user_prompt = build_user_prompt(dataset, output)
        except Exception as e:
            logger.error(f"Failed to build prompts for dataset evaluation: {e}")
            raise RuntimeError(f"Prompt builders failed: {e}")

        # Call OpenAI
        try:
            # Configure response format based on output type
            api_params = {
                "model": self.model_name,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                "temperature": 0.1,
                "max_tokens": 2048,
            }

            # Only enable JSON mode for json output
            if output == "json":
                api_params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**api_params)

            # Parse response
            response_text = response.choices[0].message.content
            logger.debug(f"OpenAI response: {response_text[:500]}...")

            # For text output, return raw text wrapped in a simple evaluation object
            if output == "text":
                return MetadataEvaluation(
                    dataset_id=None,  # Will be set by service
                    dataset_slug=None,  # Will be set by service
                    evaluated_at=datetime.now(),
                    overall_score=0.0,  # Not applicable for text format
                    criteria_scores={},  # Not applicable for text format
                    suggestions=[],  # Not applicable for text format
                    raw_text=response_text,  # Store raw text evaluation
                )

            # For JSON output, validate with Pydantic
            evaluation_data = json.loads(response_text)
            validated = EvaluationResponse(**evaluation_data)

            # Convert to domain model
            return self._to_domain_model(dataset, validated)

        except ValidationError as e:
            logger.error(f"Failed to validate OpenAI response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
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
            dataset_id=None,  # Will be set by service
            dataset_slug=None,  # Will be set by service
            evaluated_at=datetime.now(),
            overall_score=response.overall_score,
            criteria_scores=criteria_scores,
            suggestions=suggestions,
        )
