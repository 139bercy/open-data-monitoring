"""Domain exceptions for authentication bounded context."""


class UnauthorizedError(Exception):
    """Raised when authentication fails or is missing."""

    pass


class ForbiddenError(Exception):
    """Raised when authenticated user lacks required permissions."""

    pass


class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""

    pass
