"""
Dataset API Schemas
Self-documenting schemas using type annotations and minimal descriptions.
"""

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Domain Types
# ============================================================================

DatasetId = UUID
BusinessUID = str  # Unique ID from source platform (e.g., "ods:eau-2023")
DatasetSlug = str  # URL-friendly identifier
SourceURL = str
Publisher = str | None
SyncStatus = str  # 'pending' | 'success' | 'failed'

# Validated types
PositiveInt = Annotated[int, Field(ge=0)]
Score = Annotated[float, Field(ge=0.0, le=100.0)]

# ============================================================================
# List View
# ============================================================================


class DatasetAPI(BaseModel):
    """Dataset summary for list/table display."""

    # Identity
    id: DatasetId | None = None
    buid: BusinessUID
    slug: DatasetSlug
    title: str | None = None

    # Source
    page: SourceURL
    publisher: Publisher = None

    # Timestamps
    timestamp: datetime.datetime | None = None  # Last snapshot
    created: datetime.datetime
    modified: datetime.datetime

    # Flags
    published: bool
    restricted: bool
    deleted: bool = False  # Soft delete flag

    # Metrics (populated when include_counts=true)
    downloads_count: PositiveInt | None = None
    api_calls_count: PositiveInt | None = None
    views_count: PositiveInt | None = None
    reuses_count: PositiveInt | None = None
    followers_count: PositiveInt | None = None
    popularity_score: Score | None = None
    versions_count: PositiveInt = 0

    # Sync status
    last_sync: datetime.datetime | None = None
    last_sync_status: SyncStatus


# ============================================================================
# Dataset Creation
# ============================================================================


class DatasetCreateResponse(BaseModel):
    """Response after creating a new dataset via API."""

    id: DatasetId
    name: str
    timestamp: str
    buid: BusinessUID
    slug: DatasetSlug
    organization_id: str
    type: str  # Platform type
    url: SourceURL
    key: str  # API key used


# ============================================================================
# Version History
# ============================================================================


class SnapshotVersionAPI(BaseModel):
    """
    Immutable snapshot of dataset state at a point in time.
    Diffs are pre-calculated by backend for performance.
    """

    id: UUID
    timestamp: datetime.datetime
    title: str | None = None

    # Metrics at this point in time
    downloads_count: PositiveInt | None = None
    api_calls_count: PositiveInt | None = None
    views_count: PositiveInt | None = None
    reuses_count: PositiveInt | None = None
    followers_count: PositiveInt | None = None
    popularity_score: Score | None = None

    # Backend-calculated diff from previous version
    diff: dict | None = None

    # Full snapshot data (only when include_data=true)
    data: dict | None = None


# ============================================================================
# API Responses
# ============================================================================


# ============================================================================
# API Responses
# ============================================================================


class DatasetResponse(BaseModel):
    """Paginated list of datasets."""

    datasets: list[DatasetAPI]
    total_datasets: int


class DatasetDetailAPI(DatasetAPI):
    """Comprehensive dataset view with detailed quality and snapshots."""

    quality: dict | None = None
    current_snapshot: SnapshotVersionAPI | None = None
    snapshots: list[SnapshotVersionAPI] | None = None


class DatasetVersionsResponse(BaseModel):
    """Paginated list of dataset versions."""

    items: list[SnapshotVersionAPI]
    total: int
    page: int  # 1-indexed
    page_size: int
