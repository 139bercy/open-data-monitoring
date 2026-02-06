from typing import Optional, Union

from pydantic import BaseModel, Field


class CriterionScoreResponse(BaseModel):
    """LLM response for a single criterion score."""

    score: float = Field(..., ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
    category: str
    weight: float = Field(..., ge=0, le=1)


class SuggestionResponse(BaseModel):
    """LLM response for a metadata improvement suggestion."""

    field: str
    current_value: Optional[Union[str, list[str]]] = None
    suggested_value: Union[str, list[str]]
    reason: str
    priority: str = Field(..., pattern="^(high|medium|low)$")


class EvaluationResponse(BaseModel):
    """Complete LLM response for metadata evaluation."""

    overall_score: float = Field(..., ge=0, le=100)
    criteria_scores: dict[str, CriterionScoreResponse]
    suggestions: list[SuggestionResponse]
