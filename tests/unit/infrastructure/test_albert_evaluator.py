from unittest.mock import MagicMock, patch

import pytest

from infrastructure.llm.albert_evaluator import (
    DEFAULT_ALBERT_BASE_URL,
    DEFAULT_ALBERT_MODEL,
    AlbertEvaluator,
)


def test_albert_evaluator_init_with_defaults(monkeypatch):
    monkeypatch.setenv("ALBERT_API_KEY", "test-key-123")
    monkeypatch.delenv("ALBERT_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALBERT_BASE_URL", raising=False)
    monkeypatch.delenv("ALBERT_MODEL_NAME", raising=False)

    with patch("infrastructure.llm.albert_evaluator.OpenAI") as mock_openai:
        evaluator = AlbertEvaluator()
        assert evaluator.api_key == "test-key-123"
        assert evaluator.base_url == DEFAULT_ALBERT_BASE_URL
        assert evaluator.model_name == DEFAULT_ALBERT_MODEL
        mock_openai.assert_called_once_with(
            api_key="test-key-123",
            base_url=DEFAULT_ALBERT_BASE_URL,
        )


def test_albert_evaluator_init_custom_params():
    with patch("infrastructure.llm.albert_evaluator.OpenAI") as mock_openai:
        evaluator = AlbertEvaluator(
            api_key="custom-key",
            model_name="custom-model",
            base_url="https://custom.albert.url/v1",
        )
        assert evaluator.api_key == "custom-key"
        assert evaluator.model_name == "custom-model"
        assert evaluator.base_url == "https://custom.albert.url/v1"
        mock_openai.assert_called_once_with(
            api_key="custom-key",
            base_url="https://custom.albert.url/v1",
        )


def test_albert_evaluator_missing_api_key(monkeypatch):
    monkeypatch.delenv("ALBERT_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ALBERT_API_KEY must be set"):
        AlbertEvaluator()


def test_albert_evaluator_evaluate_metadata():
    with patch("infrastructure.llm.albert_evaluator.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock OpenAI response
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = """{
            "overall_score": 88.0,
            "criteria_scores": {
                "title": {
                    "category": "descriptive",
                    "score": 90.0,
                    "weight": 0.2,
                    "issues": []
                }
            },
            "suggestions": [
                {
                    "field": "title",
                    "current_value": "Short Title",
                    "suggested_value": "A more descriptive title",
                    "reason": "Clarity",
                    "priority": "high"
                }
            ]
        }"""
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        evaluator = AlbertEvaluator(api_key="dummy-key")
        dataset = {
            "title": "Test Dataset",
            "description": "A test description",
            "slug": "test-dataset",
        }

        evaluation = evaluator.evaluate_metadata(
            dataset=dataset,
            dcat_reference="# DCAT",
            charter="# Charter",
            output="json",
        )

        assert evaluation.overall_score == 88.0
        assert "title" in evaluation.criteria_scores
        assert evaluation.criteria_scores["title"].score == 90.0
        assert len(evaluation.suggestions) == 1
        assert evaluation.suggestions[0].field == "title"
        assert evaluation.suggestions[0].priority == "high"
