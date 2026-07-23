from backend.repositories import MetricsRepository
from backend.schemas import (
    AIStatusMetrics,
    EmailStatusMetrics,
    MetricsResponse,
)


class MetricsService:
    def __init__(self, repository: MetricsRepository) -> None:
        self._repository = repository

    async def get_metrics(self) -> MetricsResponse:
        snapshot = await self._repository.get_snapshot()
        return MetricsResponse(
            total_contacts=snapshot.total_contacts,
            ai=AIStatusMetrics(
                completed=snapshot.ai_completed,
                fallback=snapshot.ai_fallback,
            ),
            owner_email=EmailStatusMetrics(
                pending=snapshot.owner_email_pending,
                sent=snapshot.owner_email_sent,
                failed=snapshot.owner_email_failed,
            ),
            user_email=EmailStatusMetrics(
                pending=snapshot.user_email_pending,
                sent=snapshot.user_email_sent,
                failed=snapshot.user_email_failed,
            ),
            categories=snapshot.categories,
        )
