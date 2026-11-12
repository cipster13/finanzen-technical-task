from typing import Protocol, runtime_checkable
from pydantic import AliasPath, BaseModel, Field, ValidationError
from .models import Article
from datetime import datetime
import yfinance
from .exception import NewsUnavailableError
import logging

logger = logging.getLogger(__name__)


@runtime_checkable
class NewsProvider(Protocol):
    def fetch(self, ticker: str) -> list[Article]: ...


def _content(*keys: str) -> AliasPath:
    return AliasPath("content", *keys)


class _YFinanceArticle(BaseModel):
    title: str = Field(validation_alias=_content("title"))
    summary: str | None = Field(None, validation_alias=_content("summary"))
    description: str | None = Field(None, validation_alias=_content("description"))
    click_through_url: str | None = Field(
        None, validation_alias=_content("clickThroughUrl", "url")
    )
    canonical_url: str | None = Field(
        None, validation_alias=_content("canonicalUrl", "url")
    )
    publisher: str | None = Field(
        None, validation_alias=_content("provider", "displayName")
    )
    published_at: datetime = Field(validation_alias=_content("pubDate"))


def parse_yfinance_article(raw: dict) -> Article | None:
    try:
        item = _YFinanceArticle.model_validate(raw)
        return Article(
            title=item.title,
            summary=item.summary or item.description or None,
            url=item.click_through_url or item.canonical_url,
            publisher=item.publisher or "Unknown",
            published_at=item.published_at,
        )
    except ValidationError as e:
        bad_fields = [".".join(map(str, err["loc"])) for err in e.errors()]
        logger.warning(
            "Skipping article %s: invalid fields %s",
            raw.get("id", "<no id>"),
            bad_fields,
        )
        return None


class YFinanceProvider:

    def fetch(self, ticker: str) -> list[Article]:
        try:
            news = yfinance.Ticker(ticker).news or []
        except Exception as e:
            raise NewsUnavailableError(ticker) from e

        articles = [parse_yfinance_article(raw) for raw in news]
        return [article for article in articles if article is not None]
