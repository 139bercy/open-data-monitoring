"""
Publisher API Schemas
Self-documenting schemas using type annotations.
"""

from pydantic import BaseModel

# ============================================================================
# Domain Types
# ============================================================================

PublisherName = str

# ============================================================================
# Publisher Schemas
# ============================================================================


class PublisherStats(BaseModel):
    """Aggregated stats for a specific publisher."""

    publisher: PublisherName
    dataset_count: int

    model_config = {"arbitrary_types_allowed": True}


class PublishersResponse(BaseModel):
    """Response returned when listing all publishers."""

    publishers: list[PublisherStats]
    total_publishers: int

    model_config = {"arbitrary_types_allowed": True}
