"""Domain exceptions for platform bounded context."""


class InvalidPlatformTypeError(Exception):
    """Raised when platform type is not supported."""

    pass


class PlatformNotFoundError(Exception):
    """Raised when a platform cannot be found."""

    pass
