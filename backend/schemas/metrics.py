from pydantic import BaseModel


class AIStatusMetrics(BaseModel):
    completed: int
    fallback: int


class EmailStatusMetrics(BaseModel):
    pending: int
    sent: int
    failed: int


class MetricsResponse(BaseModel):
    total_contacts: int
    ai: AIStatusMetrics
    owner_email: EmailStatusMetrics
    user_email: EmailStatusMetrics
    categories: dict[str, int]
