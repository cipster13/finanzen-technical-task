from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class Article(BaseModel):
    title: str = Field(min_length=1)
    summary: str | None
    url: str = Field(min_length=1)
    publisher: str
    published_at: datetime


class KeyPoint(BaseModel):
    text: str = Field(description="One short, factual point a trader should know.")
    sources: list[int] = Field(
        description="Numbers of the articles this point is based on, e.g. [1, 3]."
    )


class Summary(BaseModel):
    overview: str = Field(
        description="2-3 sentences on what is happening with this stock right now."
    )
    key_points: list[KeyPoint] = Field(description="The 3-5 most important points.")
    sentiment: Literal["bullish", "bearish", "neutral", "mixed"] = Field(
        description="Overall tone of the news for the stock."
    )
