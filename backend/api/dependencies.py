from functools import lru_cache
from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import MetricsAccessDeniedError, RateLimitExceededError
from backend.core.rate_limit import InMemoryRateLimiter
from backend.core.settings import get_settings
from backend.db.session import get_session
from backend.repositories import ContactRepository, MetricsRepository
from backend.services.ai import AIService
from backend.services.contact import ContactService
from backend.services.email import EmailService
from backend.services.metrics import MetricsService


@lru_cache
def get_ai_service() -> AIService:
    return AIService(get_settings())


@lru_cache
def get_email_service() -> EmailService:
    return EmailService(get_settings())


@lru_cache
def get_rate_limiter() -> InMemoryRateLimiter:
    settings = get_settings()
    return InMemoryRateLimiter(
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


async def enforce_contact_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_ip = request.client.host if request.client is not None else "unknown"
    if settings.trust_proxy_headers:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",", maxsplit=1)[0].strip()

    retry_after = await get_rate_limiter().check(client_ip)
    if retry_after is not None:
        raise RateLimitExceededError(retry_after)


def enforce_metrics_access(
    provided_key: Annotated[
        str | None,
        Header(alias="X-Metrics-API-Key"),
    ] = None,
) -> None:
    configured_key = get_settings().metrics_api_key
    if configured_key is None:
        return

    expected_key = configured_key.get_secret_value().strip()
    if not expected_key:
        return
    if provided_key is None or not compare_digest(provided_key, expected_key):
        raise MetricsAccessDeniedError


def get_contact_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactService:
    return ContactService(
        ai_service=get_ai_service(),
        email_service=get_email_service(),
        contact_repository=ContactRepository(session),
    )


def get_metrics_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MetricsService:
    return MetricsService(MetricsRepository(session))


ContactServiceDep = Annotated[
    ContactService,
    Depends(get_contact_service),
]
MetricsServiceDep = Annotated[
    MetricsService,
    Depends(get_metrics_service),
]
