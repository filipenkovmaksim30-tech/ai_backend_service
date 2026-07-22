from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ContactCategory(StrEnum):
    PROJECT = "project"
    CONSULTATION = "consultation"
    JOB_OFFER = "job_offer"
    SUPPORT = "support"
    SPAM = "spam"
    OTHER = "other"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class AIStatus(StrEnum):
    COMPLETED = "completed"
    FALLBACK = "fallback"


class EmailStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ContactStatus(StrEnum):
    ACCEPTED = "accepted"


class ContactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=25, pattern=r"^\+?[0-9() .-]+$")
    email: EmailStr
    comment: str = Field(min_length=10, max_length=3000)

    @field_validator("name", "phone", "comment", mode="before")
    @classmethod
    def strip_surrounding_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ContactStatus = ContactStatus.ACCEPTED
    ai_status: AIStatus
    owner_email_status: EmailStatus
    user_email_status: EmailStatus
