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
from interfaces.api.schemas.errors import ProblemDetails


def register_error_handlers(app: FastAPI):
    """Register all exception handlers to the FastAPI app."""

    def create_problem_response(
        status_code: int, title: str, detail: str, type_str: str, instance: str = None, extension: dict = None
    ) -> JSONResponse:
        problem = ProblemDetails(
            type=f"/probs/{type_str}",
            title=title,
            status=status_code,
            detail=detail,
            instance=instance,
            extension=extension,
        )
        return JSONResponse(
            status_code=status_code,
            content=problem.model_dump(exclude_none=True),
            media_type="application/problem+json",
        )

    @app.exception_handler(DatasetNotFoundError)
    @app.exception_handler(PlatformNotFoundError)
    async def not_found_handler(request: Request, exc: Exception):
        return create_problem_response(
            status_code=404,
            title="Resource Not Found",
            detail=str(exc),
            type_str="not-found",
            instance=str(request.url),
        )

    @app.exception_handler(DatasetAlreadyDeletedError)
    @app.exception_handler(DatasetNotDeletedError)
    @app.exception_handler(InvalidPlatformTypeError)
    async def bad_request_handler(request: Request, exc: Exception):
        return create_problem_response(
            status_code=400, title="Bad Request", detail=str(exc), type_str="bad-request", instance=str(request.url)
        )

    @app.exception_handler(InvalidMetricValueError)
    async def validation_error_handler(request: Request, exc: InvalidMetricValueError):
        return create_problem_response(
            status_code=422,
            title="Validation Error",
            detail=str(exc),
            type_str="validation-error",
            instance=str(request.url),
            extension={"metric": exc.metric_name, "value": exc.value},
        )

    @app.exception_handler(DatasetUnreachableError)
    async def unreachable_handler(request: Request, exc: Exception):
        return create_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="The remote dataset platform is currently unreachable",
            type_str="service-unavailable",
            instance=str(request.url),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return create_problem_response(
            status_code=400, title="Value Error", detail=str(exc), type_str="value-error", instance=str(request.url)
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Log the error here if needed
        return create_problem_response(
            status_code=500,
            title="Internal Server Error",
            detail="An unexpected error occurred on the server.",
            type_str="internal-server-error",
            instance=str(request.url),
        )
