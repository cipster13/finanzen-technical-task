from pydantic import BaseModel, Field
from datetime import datetime


class Article(BaseModel):
    title: str = Field(min_length=1)
    summary: str | None
    url: str = Field(min_length=1)
    publisher: str
    published_at: datetime
