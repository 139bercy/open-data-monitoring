import json
from datetime import datetime

import requests

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

    def evaluate_metadata(
        self, dataset: Dataset, dcat_reference: str, charter: str, output: str, prompt_type: str = "standard"
    ) -> MetadataEvaluation:
        """
        Evaluate dataset metadata using Ollama.

        Args:
            dataset: Dataset to evaluate
            dcat_reference: DCAT reference (Markdown)
            charter: Open Data charter (Markdown)
            output: Choose output format between text or json
            prompt_type: Type of prompt to use (standard or light)

        Returns:
            MetadataEvaluation with scores and suggestions
        """
        dataset_name = dataset.slug if hasattr(dataset, "slug") else dataset.get("title", "unknown")
        logger.info(
            f"Evaluating metadata for dataset {dataset_name} with Ollama (output: {output}, prompt: {prompt_type})"
        )

        # Build prompts
        system_prompt = build_system_prompt(dcat_reference, charter, output, prompt_type=prompt_type)
        user_prompt = build_user_prompt(dataset, output, prompt_type=prompt_type)

        # Combine prompts for Ollama
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Call Ollama
        try:
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistency
                    "num_predict": 2048,  # Max tokens for response
                    "num_ctx": 8192,  # Increase context window
                },
            }

            if output == "json":
                payload["format"] = "json"

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=300,  # 5 minutes timeout for local inference
            )
            response.raise_for_status()

            # Parse response
            ollama_response = response.json()
            response_text = ollama_response.get("response", "")

            logger.debug(f"Ollama response: {response_text[:500]}...")

            # For text output, return raw text wrapped in a simple evaluation object
            if output == "text":
                return MetadataEvaluation(
                    dataset_id=None,  # Will be set by service
                    dataset_slug=None,  # Will be set by service
                    evaluated_at=datetime.now(),
                    overall_score=0.0,
                    criteria_scores=[],
                    suggestions=[],
                    raw_text=response_text,
                )

            # JSON Parsing
            try:
                # Basic cleaning for some LLMs that might wrap JSON in markdown blocks
                json_content = response_text.replace("```json", "").replace("```", "").strip()

                if prompt_type == "light":
                    from infrastructure.llm.models import LightEvaluationResponse

                    parsed_light = LightEvaluationResponse.model_validate_json(json_content)
                    return self._map_light_to_domain(dataset, parsed_light)

                # Standard format
                evaluation_data = json.loads(json_content)
                validated = EvaluationResponse(**evaluation_data)

                # Convert to domain model
                return self._to_domain_model(dataset, validated)

            except Exception as e:
                logger.error(f"Failed to parse Ollama JSON response: {e}")
                logger.error(f"Response was: {response_text}")
                raise ValueError(f"Invalid JSON from Ollama: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(
                f"Ollama evaluation failed: {e}. "
                "Make sure Ollama is running ('ollama serve') "
                f"and model '{self.model_name}' is installed ('ollama pull {self.model_name}')"
            )

    def _map_light_to_domain(self, dataset: Dataset, light: any) -> MetadataEvaluation:
        """Map the light prompt response format to domain MetadataEvaluation."""
        # Map light keys to standard keys
        key_map = {
            "titre": "title",
            "description": "description",
            "producteur": "producer",
            "contact": "contact",
            "mots_cles": "keywords",
            "date_pub": "publication_date",
            "licence": "license",
            "date_maj": "update_date",
            "refs": "references",
            "freq": "update_frequency",
            "spatial": "spatial_coverage",
            "temporel": "temporal_coverage",
        }

        # Standard weights
        weights = {
            "title": 0.10,
            "description": 0.15,
            "producer": 0.05,
            "contact": 0.05,
            "keywords": 0.05,
            "publication_date": 0.05,
            "license": 0.10,
            "update_date": 0.05,
            "references": 0.10,
            "update_frequency": 0.10,
            "spatial_coverage": 0.10,
            "temporal_coverage": 0.10,
        }

        categories = {
            "title": "descriptive",
            "description": "descriptive",
            "producer": "descriptive",
            "contact": "descriptive",
            "keywords": "descriptive",
            "publication_date": "administrative",
            "license": "administrative",
            "update_date": "administrative",
            "references": "administrative",
            "update_frequency": "geotemporal",
            "spatial_coverage": "geotemporal",
            "temporal_coverage": "geotemporal",
        }

        criteria_scores = {}
        overall_score = 0.0

        for light_key, score in light.scores.items():
            std_key = key_map.get(light_key, light_key)
            weight = weights.get(std_key, 0.0)
            category = categories.get(std_key, "unknown")

            # Find issues related to this field
            field_issues = [i.issue for i in light.issues if i.field == light_key]

            criteria_scores[std_key] = CriterionScore(
                criterion=std_key,
                score=float(score),
                issues=field_issues,
                category=category,
                weight=weight,
            )
            overall_score += float(score) * weight

        suggestions = [
            Suggestion(
                field=key_map.get(i.field, i.field),
                current_value=None,  # Not provided in light format
                suggested_value=i.fix,
                reason=i.issue,
                priority=i.priority,
            )
            for i in light.issues
        ]

        return MetadataEvaluation(
            dataset_id=None,
            dataset_slug=None,
            evaluated_at=datetime.now(),
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            suggestions=suggestions,
        )

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
