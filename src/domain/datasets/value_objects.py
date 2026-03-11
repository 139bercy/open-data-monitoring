from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from domain.datasets.kpis import DiscoverabilityKPI, ImpactKPI


@dataclass
class DatasetQuality:
    downloads_count: Optional[int]
    api_calls_count: Optional[int]
    has_description: bool
    is_slug_valid: bool
    evaluation_results: Optional[dict] = None
    discoverability: Optional[DiscoverabilityKPI] = None
    impact: Optional[ImpactKPI] = None
    syntax_change_score: Optional[float] = None
    evaluated_blob_id: Optional[UUID] = None
    health_score: Optional[float] = None
    health_quality_score: Optional[float] = None
    health_freshness_score: Optional[float] = None
    health_engagement_score: Optional[float] = None


@dataclass(frozen=True)
class DatasetVersionParams:
    """Parameter object for dataset version creation.

    Replaces the 11-parameter add_version method signature with a single,
    cohesive object that groups all version-related data.
    """

    dataset_id: UUID
    snapshot: dict
    checksum: Optional[str]
    title: str
    downloads_count: Optional[int] = None
    api_calls_count: Optional[int] = None
    views_count: Optional[int] = None
    reuses_count: Optional[int] = None
    followers_count: Optional[int] = None
    popularity_score: Optional[float] = None
    diff: Optional[dict] = None
