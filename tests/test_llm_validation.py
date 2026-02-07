import pytest
from pydantic import ValidationError

from domain.quality.evaluation import Suggestion
from infrastructure.llm.models import EvaluationResponse, SuggestionResponse


@pytest.mark.parametrize(
    "current, suggested",
    [
        ("Old Title", "New Title"),
        (["tag1", "tag2"], ["tag1", "tag2", "tag3"]),
        (None, "Initial description"),
        (["old"], "new string"),
        ("old string", ["new", "list"]),
    ],
)
def test_suggestion_response_supports_mixed_types(current, suggested):
    """Verify that SuggestionResponse accepts both strings and lists for current/suggested values."""
    s = SuggestionResponse(
        field="any_field", current_value=current, suggested_value=suggested, reason="reason", priority="high"
    )
    assert s.current_value == current
    assert s.suggested_value == suggested


def test_evaluation_response_parsing():
    """Verify that a complete EvaluationResponse can be parsed with mixed suggestion types."""
    data = {
        "overall_score": 85.0,
        "criteria_scores": {"title": {"score": 90.0, "issues": [], "category": "descriptive", "weight": 0.2}},
        "suggestions": [
            {
                "field": "title",
                "current_value": "Short",
                "suggested_value": "Longer and better",
                "reason": "Too short",
                "priority": "high",
            },
            {
                "field": "keywords",
                "current_value": ["A", "B"],
                "suggested_value": ["A", "B", "C"],
                "reason": "Missing C",
                "priority": "low",
            },
        ],
    }

    validated = EvaluationResponse(**data)
    assert len(validated.suggestions) == 2
    assert isinstance(validated.suggestions[0].suggested_value, str)
    assert isinstance(validated.suggestions[1].suggested_value, list)


@pytest.mark.parametrize(
    "current, suggested",
    [
        ("Old", "New"),
        (["A"], ["B"]),
        (None, ["new"]),
    ],
)
def test_domain_suggestion_accepts_mixed_types(current, suggested):
    """Verify that the domain Suggestion entity also supports mixed types."""
    s = Suggestion(field="tags", current_value=current, suggested_value=suggested, reason="updated", priority="medium")
    assert s.current_value == current
    assert s.suggested_value == suggested


def test_suggestion_response_invalid_priority():
    """Verify that invalid priority still raises ValidationError."""
    with pytest.raises(ValidationError):
        SuggestionResponse(field="field", suggested_value="val", reason="reason", priority="invalid")
