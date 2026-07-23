import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.core.exceptions import (
    DatabaseOperationError,
    MetricsAccessDeniedError,
    RateLimitExceededError,
)

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def validation_error_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    details = [
        {
            "location": list(item["loc"]),
            "message": item["msg"],
            "type": item["type"],
        }
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": details,
            },
            "request_id": _request_id(request),
        },
    )


async def database_error_handler(
    request: Request,
    error: DatabaseOperationError,
) -> JSONResponse:
    logger.error(
        "Database operation failed",
        extra={
            "request_id": _request_id(request),
            "error_type": type(error).__name__,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "database_unavailable",
                "message": "Service is temporarily unavailable",
            },
            "request_id": _request_id(request),
        },
    )


async def unexpected_error_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    logger.error(
        "Unexpected application error",
        exc_info=(type(error), error, error.__traceback__),
        extra={
            "request_id": _request_id(request),
            "error_type": type(error).__name__,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred",
            },
            "request_id": _request_id(request),
        },
    )


async def rate_limit_error_handler(
    request: Request,
    error: RateLimitExceededError,
) -> JSONResponse:
    logger.warning(
        "Rate limit exceeded",
        extra={"request_id": _request_id(request)},
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(error.retry_after)},
        content={
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests",
            },
            "request_id": _request_id(request),
        },
    )


async def metrics_access_denied_handler(
    request: Request,
    _error: MetricsAccessDeniedError,
) -> JSONResponse:
    logger.warning(
        "Metrics access denied",
        extra={"request_id": _request_id(request)},
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": "metrics_access_denied",
                "message": "Metrics access denied",
            },
            "request_id": _request_id(request),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        DatabaseOperationError,
        database_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RateLimitExceededError,
        rate_limit_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        MetricsAccessDeniedError,
        metrics_access_denied_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        Exception,
        unexpected_error_handler,
    )
