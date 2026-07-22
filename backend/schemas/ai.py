from pydantic import BaseModel, Field

from backend.schemas.contact import ContactCategory, Sentiment


class AIAnalysis(BaseModel):
    category: ContactCategory
    sentiment: Sentiment
    summary: str = Field(min_length=1, max_length=500)
