from typing import Protocol, runtime_checkable
from pydantic import ValidationError
from .models import Article
import yfinance
from .exception import NewsUnavailableError
import logging

logger = logging.getLogger(__name__)


@runtime_checkable
class NewsProvider(Protocol):
    def fetch(self, ticker: str) -> list[Article]: ...


def parse_yfinance_article(raw: dict) -> Article | None:
    content = raw.get("content") or {}
    url = (content.get("clickThroughUrl") or {}).get("url") or (
        content.get("canonicalUrl") or {}
    ).get("url")
    try:
        return Article(
            title=content.get("title"),
            summary=content.get("summary") or content.get("description") or None,
            url=url,
            publisher=(content.get("provider") or {}).get("displayName") or "Unknown",
            published_at=content.get("pubDate"),
        )
    except ValidationError as e:
        logger.error(
            "Error while parsing the article %s, with error message %s", raw, e
        )
        return None


class YFinanceProvider:

    def fetch(self, ticker: str) -> list[Article]:
        try:
            news = yfinance.Ticker(ticker).news
        except Exception as e:
            raise NewsUnavailableError from e

        articles = [parse_yfinance_article(raw) for raw in news]
        return [article for article in articles if article is not None]
