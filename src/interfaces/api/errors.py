"""
Centralized exception handling for the FastAPI application.
Maps Domain exceptions to appropriate HTTP status codes.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.datasets.exceptions import (
    DatasetAlreadyDeletedError,
    DatasetNotDeletedError,
    DatasetNotFoundError,
    DatasetUnreachableError,
    InvalidMetricValueError,
)
from domain.platform.exceptions import InvalidPlatformTypeError, PlatformNotFoundError


def register_error_handlers(app: FastAPI):
    """Register all exception handlers to the FastAPI app."""

    @app.exception_handler(DatasetNotFoundError)
    @app.exception_handler(PlatformNotFoundError)
    async def not_found_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "type": exc.__class__.__name__},
        )

    @app.exception_handler(DatasetAlreadyDeletedError)
    @app.exception_handler(DatasetNotDeletedError)
    @app.exception_handler(InvalidPlatformTypeError)
    async def bad_request_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "type": exc.__class__.__name__},
        )

    @app.exception_handler(InvalidMetricValueError)
    async def validation_error_handler(request: Request, exc: InvalidMetricValueError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": str(exc),
                "type": exc.__class__.__name__,
                "metric": exc.metric_name,
                "value": exc.value,
            },
        )

    @app.exception_handler(DatasetUnreachableError)
    async def unreachable_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=503,
            content={"detail": "The remote dataset platform is currently unreachable", "type": exc.__class__.__name__},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        # ValueErrors from repositories often mean "Not Found" or "Bad Request"
        # Since we use them for registration or lookup, we return 400
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "type": "ValueError"},
        )
