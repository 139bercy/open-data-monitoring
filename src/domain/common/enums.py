"""Common enums used across domain bounded contexts."""

from enum import Enum


class SyncStatus(str, Enum):
    """Synchronization status for platforms and datasets.

    Inherits from str to maintain compatibility with existing string comparisons
    and database storage while providing type safety.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return the string value for database storage and serialization."""
        return self.value


class PlatformType(str, Enum):
    """Supported open data platform types.

    Inherits from str to maintain compatibility with existing string comparisons
    and database storage while providing type safety.
    """

    OPENDATASOFT = "opendatasoft"
    DATAGOUV = "datagouv"

    def __str__(self) -> str:
        """Return the string value for database storage and serialization."""
        return self.value
