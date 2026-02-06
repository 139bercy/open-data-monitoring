from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union
from uuid import UUID


@dataclass
class CriterionScore:
    """Score for a single evaluation criterion."""

    criterion: str
    category: str  # "descriptive", "administrative", "geotemporal"
    score: float  # 0-100
    weight: float  # Weight in overall score
    issues: list[str] = field(default_factory=list)

    def weighted_score(self) -> float:
        """Calculate weighted contribution to overall score."""
        return self.score * self.weight


@dataclass
class Suggestion:
    """Improvement suggestion for a metadata field."""

    field: str
    current_value: Optional[Union[str, list[str]]]
    suggested_value: Union[str, list[str]]
    reason: str
    priority: str  # "high", "medium", "low"


@dataclass
class MetadataEvaluation:
    """Complete evaluation of dataset metadata quality."""

    dataset_id: UUID
    dataset_slug: str
    evaluated_at: datetime
    overall_score: float  # 0-100
    criteria_scores: dict[str, CriterionScore]
    suggestions: list[Suggestion]
    raw_text: Optional[str] = None  # For text-format evaluations

    def get_scores_by_category(self, category: str) -> list[CriterionScore]:
        """Get all criterion scores for a specific category."""
        return [score for score in self.criteria_scores.values() if score.category == category]

    def get_high_priority_suggestions(self) -> list[Suggestion]:
        """Get only high priority suggestions."""
        return [s for s in self.suggestions if s.priority == "high"]
