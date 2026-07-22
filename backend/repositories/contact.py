
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.contact import Contact
from backend.core.exceptions import DatabaseOperationError

class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, contact: Contact) -> Contact:
        try:
            self._session.add(contact)
            await self._session.commit() 
            await self._session.refresh(contact)
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DatabaseOperationError("Database operation failed") from error
        return contact

    async def update_email_statuses(self, contact: Contact, *, owner_status: str, user_status: str) -> Contact:
        try:
            contact.owner_email_status = owner_status
            contact.user_email_status = user_status

            await self._session.commit()
            await self._session.refresh(contact)
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DatabaseOperationError(
                "Database operation failed"
            ) from error

        return contact
                    
