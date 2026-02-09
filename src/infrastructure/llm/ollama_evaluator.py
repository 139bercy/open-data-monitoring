import json
from datetime import datetime

import requests
from pydantic import ValidationError

from domain.datasets.aggregate import Dataset
from domain.quality.evaluation import CriterionScore, MetadataEvaluation, Suggestion
from domain.quality.ports import LLMEvaluator
from infrastructure.llm.models import EvaluationResponse
from infrastructure.llm.prompts import build_system_prompt, build_user_prompt
from logger import logger


class OllamaEvaluator(LLMEvaluator):
    """Ollama-based metadata quality evaluator (local LLM)."""

    def __init__(self, model_name: str = "llama3.1", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama evaluator.

        Args:
            model_name: Ollama model to use (default: llama3.1)
            base_url: Ollama API base URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

        # Check if Ollama is running
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            response.raise_for_status()
            logger.info(f"Connected to Ollama at {base_url}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama not reachable at {base_url}: {e}")
            logger.warning("Make sure Ollama is running: 'ollama serve'")

    def evaluate_metadata(self, dataset: Dataset, dcat_reference: str, charter: str) -> MetadataEvaluation:
        """
        Evaluate dataset metadata using Ollama.

        Args:
            dataset: Dataset to evaluate
            dcat_reference: DCAT reference (Markdown)
            charter: Open Data charter (Markdown)

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        logger.info(f"Evaluating metadata for dataset {dataset.slug} with Ollama")

        # Build prompts
        system_prompt = build_system_prompt(dcat_reference, charter)
        user_prompt = build_user_prompt(dataset)

        # Combine prompts for Ollama
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Call Ollama
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json",  # Request JSON output
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "num_predict": 2048,  # Max tokens for response
                        "num_ctx": 8192,  # Increase context window
                    },
                },
                timeout=300,  # 5 minutes timeout for local inference
            )
            response.raise_for_status()

            # Parse response
            ollama_response = response.json()
            response_text = ollama_response.get("response", "")

            logger.debug(f"Ollama response: {response_text[:500]}...")

            # Validate with Pydantic
            evaluation_data = json.loads(response_text)
            validated = EvaluationResponse(**evaluation_data)

            # Convert to domain model
            return self._to_domain_model(dataset, validated)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(
                f"Ollama evaluation failed: {e}. "
                "Make sure Ollama is running ('ollama serve') "
                f"and model '{self.model_name}' is installed ('ollama pull {self.model_name}')"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON response: {e}")
            logger.error(f"Response was: {response_text}")
            raise ValueError(f"Invalid JSON from Ollama: {e}")
        except ValidationError as e:
            logger.error(f"Failed to validate Ollama response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")

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
