from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiscoverabilityKPI:
    """
    KPI measuring how easily a dataset can be found and understood.
    Based on the ministerial Open Data Charter.
    """

    seo_score: float  # 0-100, based on title length (5-10 words)
    dcat_completeness_score: float  # 0-100, based on presence of mandatory fields
    freshness_score: float  # 0-100, based on modification date vs expected frequency
    semantic_quality_score: Optional[float] = None  # 0-100, qualitative analysis by IA
    overall_discoverability_score: float = 0.0

    def __post_init__(self):
        # Calculate overall score if not provided
        if self.overall_discoverability_score == 0.0:
            scores = [self.seo_score, self.dcat_completeness_score, self.freshness_score]
            if self.semantic_quality_score is not None:
                scores.append(self.semantic_quality_score)

            # Use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, "overall_discoverability_score", sum(scores) / len(scores))


@dataclass(frozen=True)
class ImpactKPI:
    """
    KPI measuring the actual usage and engagement of a dataset.
    """

    engagement_rate: float  # reuses / views
    usage_intensity: float  # api_calls / downloads
    popularity_score: float  # normalized score 0-100
    trend_score: float = 0.0  # evolution over last snapshots (-100 to 100)
    overall_impact_score: float = 0.0

    def __post_init__(self):
        # Calculate overall score if not provided
        if self.overall_impact_score == 0.0:
            scores = [self.engagement_rate * 100, self.usage_intensity * 100, self.popularity_score]
            # Simple average for now
            object.__setattr__(self, "overall_impact_score", sum(scores) / 3)
