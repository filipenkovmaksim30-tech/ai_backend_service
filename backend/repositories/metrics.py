from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import DatabaseOperationError
from backend.db.models import Contact


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    total_contacts: int
    ai_completed: int
    ai_fallback: int
    owner_email_pending: int
    owner_email_sent: int
    owner_email_failed: int
    user_email_pending: int
    user_email_sent: int
    user_email_failed: int
    categories: dict[str, int]


class MetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_snapshot(self) -> MetricsSnapshot:
        aggregate_query = select(
            func.count(Contact.id).label("total_contacts"),
            func.count(Contact.id)
            .filter(Contact.ai_status == "completed")
            .label("ai_completed"),
            func.count(Contact.id)
            .filter(Contact.ai_status == "fallback")
            .label("ai_fallback"),
            func.count(Contact.id)
            .filter(Contact.owner_email_status == "pending")
            .label("owner_email_pending"),
            func.count(Contact.id)
            .filter(Contact.owner_email_status == "sent")
            .label("owner_email_sent"),
            func.count(Contact.id)
            .filter(Contact.owner_email_status == "failed")
            .label("owner_email_failed"),
            func.count(Contact.id)
            .filter(Contact.user_email_status == "pending")
            .label("user_email_pending"),
            func.count(Contact.id)
            .filter(Contact.user_email_status == "sent")
            .label("user_email_sent"),
            func.count(Contact.id)
            .filter(Contact.user_email_status == "failed")
            .label("user_email_failed"),
        )
        categories_query = (
            select(Contact.category, func.count(Contact.id))
            .group_by(Contact.category)
            .order_by(Contact.category)
        )

        try:
            aggregate = (await self._session.execute(aggregate_query)).one()
            category_rows = (await self._session.execute(categories_query)).all()
        except (SQLAlchemyError, OSError) as error:
            await self._session.rollback()
            raise DatabaseOperationError("Metrics query failed") from error

        return MetricsSnapshot(
            total_contacts=aggregate.total_contacts,
            ai_completed=aggregate.ai_completed,
            ai_fallback=aggregate.ai_fallback,
            owner_email_pending=aggregate.owner_email_pending,
            owner_email_sent=aggregate.owner_email_sent,
            owner_email_failed=aggregate.owner_email_failed,
            user_email_pending=aggregate.user_email_pending,
            user_email_sent=aggregate.user_email_sent,
            user_email_failed=aggregate.user_email_failed,
            categories={category: count for category, count in category_rows},
        )
