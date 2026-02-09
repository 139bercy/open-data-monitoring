from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class DatasetQuality:
    downloads_count: Optional[int]
    api_calls_count: Optional[int]
    has_description: bool
    is_slug_valid: bool
    evaluation_results: Optional[dict] = None


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
