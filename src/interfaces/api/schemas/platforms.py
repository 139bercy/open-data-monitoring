from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Domain Types
# ============================================================================

PlatformId = Annotated[UUID, Field(description="Unique internal identifier for the platform")]
OrganizationId = Annotated[str, Field(description="External organization identifier from the source platform")]
PlatformSlug = Annotated[str, Field(description="URL-friendly identifier for the platform")]
PlatformType = Annotated[
    str, Field(description="Platform engine type (e.g., 'opendatasoft', 'datagouv')", examples=["opendatasoft"])
]
SyncStatus = Annotated[
    str, Field(description="Status of the last synchronization process", examples=["success", "failed", "pending"])
]
URL = Annotated[str, Field(description="Base URL of the data platform")]
APIKey = Annotated[str, Field(description="Secure API key for authentication")]

# ============================================================================
# Sync History
# ============================================================================


class PlatformSync(BaseModel):
    """Execution record of a single synchronization event."""

    platform_id: PlatformId
    timestamp: datetime = Field(..., description="When the sync started")
    status: SyncStatus
    datasets_count: int = Field(..., description="Number of datasets discovered during this sync", ge=0)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Platform DTOs
# ============================================================================


class PlatformDTO(BaseModel):
    """Complete platform configuration and current operational state."""

    # Identity
    id: PlatformId
    name: str = Field(..., description="Display name of the platform")
    slug: PlatformSlug
    type: PlatformType

    # Configuration
    url: URL
    organization_id: OrganizationId
    key: APIKey | None = Field(None, description="Masked API key for secure communication")

    # State & Metrics
    datasets_count: int = Field(0, description="Total number of datasets locally indexed", ge=0)
    last_sync: datetime | None = Field(None, description="Timestamp of the most recent successful sync")
    last_sync_status: SyncStatus | None = None
    created_at: datetime | None = None

    # History
    syncs: list[PlatformSync] | None = Field(None, description="Chronological history of sync attempts")

    model_config = ConfigDict(from_attributes=True)


class PlatformCreateDTO(BaseModel):
    """Input parameters for registering a new data platform in the system."""

    name: str = Field(..., min_length=1)
    slug: PlatformSlug
    organization_id: OrganizationId
    type: PlatformType
    url: URL
    key: APIKey


class PlatformCreateResponse(BaseModel):
    """Result returned after successful platform registration."""

    id: PlatformId
    name: str
    slug: PlatformSlug
    type: PlatformType
    url: URL
    key: APIKey | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API Responses
# ============================================================================


class PlatformsResponse(BaseModel):
    """Standardized response for platform listings."""

    platforms: list[PlatformDTO]
    total_platforms: int = Field(..., ge=0)
