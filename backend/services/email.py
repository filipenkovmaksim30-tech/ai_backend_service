import asyncio
import logging
from dataclasses import dataclass
from email.message import EmailMessage

import aiosmtplib
from aiosmtplib.errors import SMTPException

from backend.core.settings import Settings
from backend.db.models import Contact
from backend.schemas import EmailStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EmailResult:
    owner_status: EmailStatus
    user_status: EmailStatus


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._username = settings.smtp_username
        self._password = (
            settings.smtp_password.get_secret_value()
            if settings.smtp_password is not None
            else None
        )
        self._sender_email = (
            str(settings.smtp_sender_email)
            if settings.smtp_sender_email is not None
            else None
        )
        self._owner_email = (
            str(settings.smtp_owner_email)
            if settings.smtp_owner_email is not None
            else None
        )
        self._start_tls = settings.smtp_start_tls
        self._use_tls = settings.smtp_use_tls
        self._timeout = settings.smtp_timeout_seconds

    async def send_notifications(self, contact: Contact) -> EmailResult:
        if not self._is_configured:
            logger.warning("SMTP is not configured; notifications were not sent")
            return EmailResult(
                owner_status=EmailStatus.FAILED,
                user_status=EmailStatus.FAILED,
            )

        owner_status, user_status = await asyncio.gather(
            self._send_owner_email(contact),
            self._send_user_email(contact),
        )
        return EmailResult(
            owner_status=owner_status,
            user_status=user_status,
        )

    @property
    def _is_configured(self) -> bool:
        return bool(self._host and self._sender_email and self._owner_email)

    async def _send_owner_email(self, contact: Contact) -> EmailStatus:
        message = EmailMessage()
        message["From"] = self._sender_email
        message["To"] = self._owner_email
        message["Subject"] = "New portfolio contact request"
        message.set_content(
            "\n".join(
                (
                    f"Name: {contact.name}",
                    f"Phone: {contact.phone}",
                    f"Email: {contact.email}",
                    f"Category: {contact.category}",
                    f"Sentiment: {contact.sentiment}",
                    f"AI summary: {contact.ai_summary}",
                    "",
                    "Comment:",
                    contact.comment,
                )
            )
        )
        return await self._send(
            message,
            recipient=self._owner_email,
            notification_type="owner",
        )

    async def _send_user_email(self, contact: Contact) -> EmailStatus:
        message = EmailMessage()
        message["From"] = self._sender_email
        message["To"] = contact.email
        message["Subject"] = "Your message has been received"
        message.set_content(
            f"Hello, {contact.name}!\n\n"
            "Thank you for your message. It has been received, and I will "
            "contact you as soon as possible.\n"
        )
        return await self._send(
            message,
            recipient=contact.email,
            notification_type="user",
        )

    async def _send(
        self,
        message: EmailMessage,
        *,
        recipient: str | None,
        notification_type: str,
    ) -> EmailStatus:
        if recipient is None or self._host is None or self._sender_email is None:
            return EmailStatus.FAILED

        try:
            recipient_errors, _ = await aiosmtplib.send(
                message,
                sender=self._sender_email,
                recipients=[recipient],
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                timeout=self._timeout,
                use_tls=self._use_tls,
                start_tls=self._start_tls,
            )
            if recipient_errors:
                logger.warning(
                    "SMTP rejected a notification recipient",
                    extra={"notification_type": notification_type},
                )
                return EmailStatus.FAILED
        except (SMTPException, OSError, TimeoutError) as error:
            logger.warning(
                "SMTP notification failed",
                extra={
                    "notification_type": notification_type,
                    "error_type": type(error).__name__,
                },
            )
            return EmailStatus.FAILED

        return EmailStatus.SENT
