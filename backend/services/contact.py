from backend.db.models import Contact
from backend.repositories import ContactRepository
from backend.schemas import ContactCreate, ContactResponse
from backend.services.ai import AIService
from backend.services.email import EmailService


class ContactService:
    def __init__(
        self,
        ai_service: AIService,
        email_service: EmailService,
        contact_repository: ContactRepository,
    ) -> None:
        self._ai_service = ai_service
        self._email_service = email_service
        self._contact_repository = contact_repository

    async def create_contact(
        self,
        payload: ContactCreate,
    ) -> ContactResponse:
        ai_result = await self._ai_service.analyze(payload.comment)

        contact = Contact(
            name=payload.name,
            phone=payload.phone,
            email=str(payload.email),
            comment=payload.comment,
            category=ai_result.analysis.category.value,
            sentiment=ai_result.analysis.sentiment.value,
            ai_summary=ai_result.analysis.summary,
            ai_status=ai_result.status.value,
        )
        contact = await self._contact_repository.create(contact)

        email_result = await self._email_service.send_notifications(contact)

        contact = await self._contact_repository.update_email_statuses(
            contact,
            owner_status=email_result.owner_status.value,
            user_status=email_result.user_status.value,
        )

        return ContactResponse.model_validate(contact)