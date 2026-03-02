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
    current_value: str | list[str] | None = None
    suggested_value: str | list[str]
    reason: str
    priority: str = Field(..., pattern="^(high|medium|low)$")


class EvaluationResponse(BaseModel):
    """Complete LLM response for metadata evaluation."""

    overall_score: float = Field(..., ge=0, le=100)
    criteria_scores: dict[str, CriterionScoreResponse]
    suggestions: list[SuggestionResponse]


class LightIssueResponse(BaseModel):
    """LLM response for a single issue in the light format."""

    field: str
    issue: str
    fix: str
    priority: str = Field(..., pattern="^(high|medium|low)$")


class LightEvaluationResponse(BaseModel):
    """Complete LLM response for metadata evaluation in the light format."""

    overall_score: float = 0.0
    scores: dict[str, float]
    issues: list[LightIssueResponse]
