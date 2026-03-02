"""Gemini-based implementation of LLM metadata evaluator."""

import json
import os
from datetime import datetime

from google import genai
from pydantic import ValidationError

from domain.datasets.aggregate import Dataset
from domain.quality.evaluation import CriterionScore, MetadataEvaluation, Suggestion
from domain.quality.ports import LLMEvaluator
from infrastructure.llm.models import EvaluationResponse
from infrastructure.llm.prompts import build_system_prompt, build_user_prompt
from logger import logger


class GeminiEvaluator(LLMEvaluator):
    """Gemini-based metadata quality evaluator."""

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-pro"):
        """
        Initialize Gemini evaluator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def evaluate_metadata(
        self, dataset: Dataset, dcat_reference: str, charter: str, output: str, prompt_type: str = "standard"
    ) -> MetadataEvaluation:
        """
        Evaluate dataset metadata using Gemini.

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
            f"Evaluating metadata for dataset {dataset_name} with Gemini (output: {output}, prompt: {prompt_type})"
        )

        # Build prompts
        system_prompt = build_system_prompt(dcat_reference, charter, output, prompt_type=prompt_type)
        user_prompt = build_user_prompt(dataset, output, prompt_type=prompt_type)

        # Call Gemini
        try:
            generation_config = {"temperature": 0.1}
            if output == "json":
                generation_config["response_mime_type"] = "application/json"

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[system_prompt, user_prompt],
                config=genai.GenerationConfig(**generation_config),
            )

            # Parse response
            response_text = response.text
            logger.debug(f"Gemini response: {response_text}")

            # For text output, return raw text wrapped in a simple evaluation object
            if output == "text":
                return MetadataEvaluation(
                    dataset_id=None,  # Will be set by service
                    dataset_slug=None,  # Will be set by service
                    evaluated_at=datetime.now(),
                    overall_score=0.0,
                    criteria_scores={},
                    suggestions=[],
                    raw_text=response_text,
                )

            # JSON Parsing
            try:
                # Basic cleaning
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
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Response was: {response_text}")
                raise ValueError(f"Invalid JSON from Gemini: {e}")

        except ValidationError as e:
            logger.error(f"Failed to validate Gemini response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"LLM evaluation failed: {e}")

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
