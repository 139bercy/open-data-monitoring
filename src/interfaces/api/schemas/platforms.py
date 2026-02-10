"""
Platform API Schemas
Self-documenting schemas using type annotations and minimal descriptions.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# ============================================================================
# Domain Types
# ============================================================================

PlatformId = UUID
OrganizationId = str
PlatformSlug = str
PlatformType = str  # 'opendatasoft' | 'datagouv'
SyncStatus = str  # 'success' | 'failed' | 'pending'
URL = str
APIKey = str

# ============================================================================
# Sync History
# ============================================================================


class PlatformSync(BaseModel):
    """Execution record of a single synchronization."""

    platform_id: PlatformId
    timestamp: datetime
    status: SyncStatus
    datasets_count: int


# ============================================================================
# Platform DTOs
# ============================================================================


class PlatformDTO(BaseModel):
    """Complete platform configuration and current state."""

    # Identity
    id: PlatformId
    name: str
    slug: PlatformSlug
    type: PlatformType

    # Configuration
    url: URL
    organization_id: OrganizationId
    key: APIKey | None = None  # Masked in public responses

    # State & Metrics
    datasets_count: int = 0
    last_sync: datetime | None = None
    last_sync_status: SyncStatus | None = None
    created_at: datetime | None = None

    # History
    syncs: list[PlatformSync] | None = None

    model_config = {"arbitrary_types_allowed": True}


class PlatformCreateDTO(BaseModel):
    """Input data for registering a new platform."""

    name: str
    slug: PlatformSlug
    organization_id: OrganizationId
    type: PlatformType
    url: URL
    key: APIKey


class PlatformCreateResponse(BaseModel):
    """Response returned after successful platform registration."""

    id: PlatformId
    name: str
    slug: PlatformSlug
    type: PlatformType
    url: URL
    key: APIKey

    model_config = {"arbitrary_types_allowed": True}


# ============================================================================
# API Responses
# ============================================================================


class PlatformsResponse(BaseModel):
    """Paginated or grouped list of platforms."""

    platforms: list[PlatformDTO]
    total_platforms: int

    model_config = {"arbitrary_types_allowed": True}
