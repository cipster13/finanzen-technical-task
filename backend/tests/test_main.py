import logging
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.dependency import get_llm_client, get_news_provider
from app.exception import NewsUnavailableError, SummaryUnavailableError
from app.main import app
from app.models import Article, KeyPoint, Summary


def create_article(title: str) -> Article:
    return Article(
        title=title,
        summary="Some blurb.",
        url=f"https://example.com/{title.lower()}",
        publisher="Reuters",
        published_at=datetime(2026, 11, 9, 14, 30, tzinfo=timezone.utc),
    )


DEFAULT_SUMMARY = Summary(
    overview="Apple had a strong week.",
    key_points=[KeyPoint(text="Earnings beat", sources=[1])],
    sentiment="bullish",
)


class FakeNewsProvider:
    def __init__(self, articles: list[Article] | None = None, error=None):
        self._articles = articles or []
        self._error = error
        self.requested = []

    def fetch(self, ticker: str) -> list[Article]:
        self.requested.append(ticker)
        if self._error is not None:
            raise self._error
        return self._articles


class FakeLLMClient:
    def __init__(self, result: Summary | None = DEFAULT_SUMMARY, error=None):
        self._result = result
        self._error = error
        self.calls = 0

    def complete(self, system, user, response_model):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


@pytest.fixture
def setup_app():
    def setup(
        provider: FakeNewsProvider | None = None, llm: FakeLLMClient | None = None
    ):
        provider = provider or FakeNewsProvider(
            articles=[create_article("First"), create_article("Second")]
        )
        llm = llm or FakeLLMClient()
        app.dependency_overrides[get_news_provider] = lambda: provider
        app.dependency_overrides[get_llm_client] = lambda: llm
        client = TestClient(app, raise_server_exceptions=False)
        return client, provider, llm

    yield setup
    app.dependency_overrides.clear()


class TestGetSummarySuccess:
    def test_ticker_is_uppercased(self, setup_app):
        client, provider, _ = setup_app()

        body = client.get("/news/aapl/summary").json()

        assert body["ticker"] == "AAPL"
        assert provider.requested == ["AAPL"]

    def test_returns_200_with_summary_and_articles(self, setup_app):
        client, _, _ = setup_app()

        response = client.get("/news/AAPL/summary")

        assert response.status_code == 200
        body = response.json()
        assert body["ticker"] == "AAPL"
        assert body["summary"] == {
            "overview": "Apple had a strong week.",
            "key_points": [{"text": "Earnings beat", "sources": [1]}],
            "sentiment": "bullish",
        }
        assert [a["title"] for a in body["articles"]] == ["First", "Second"]

    def test_generated_at_is_a_utc_timestamp(self, setup_app):
        client, _, _ = setup_app()

        body = client.get("/news/AAPL/summary").json()

        assert body["generated_at"].endswith("Z")
        generated_at = datetime.fromisoformat(
            body["generated_at"].replace("Z", "+00:00")
        )
        assert generated_at.utcoffset().total_seconds() == 0

    def test_passes_the_ticker_to_the_news_provider(self, setup_app):
        client, provider, _ = setup_app()

        client.get("/news/MSFT/summary")

        assert provider.requested == ["MSFT"]

    def test_invalid_citations_are_removed_from_the_response(self, setup_app):
        llm = FakeLLMClient(
            result=Summary(
                overview="o",
                key_points=[
                    KeyPoint(text="Real", sources=[2]),
                    KeyPoint(text="Invented", sources=[9]),
                ],
                sentiment="mixed",
            )
        )
        client, _, _ = setup_app(llm=llm)

        body = client.get("/news/AAPL/summary").json()

        assert body["summary"]["key_points"] == [{"text": "Real", "sources": [2]}]

    def test_no_news_returns_200_with_null_summary(self, setup_app):
        client, _, llm = setup_app(provider=FakeNewsProvider(articles=[]))

        response = client.get("/news/ZZZZZ/summary")

        assert response.status_code == 200
        assert response.json()["summary"] is None
        assert response.json()["articles"] == []
        assert llm.calls == 0

    @pytest.mark.parametrize("ticker", ["aapl", "BRK.B", "BRK-B", "7203", "A"])
    def test_accepts_valid_ticker_formats(self, setup_app, ticker):
        client, _, _ = setup_app()

        response = client.get(f"/news/{ticker}/summary")

        assert response.status_code == 200


class TestGetSummaryBadRequests:
    @pytest.mark.parametrize(
        "ticker",
        [
            pytest.param("AA$PL", id="symbol"),
            pytest.param("AA%20PL", id="space"),
            pytest.param("ABCDEFGHIJK", id="too-long"),
            pytest.param("%3Carticles%3E", id="tag-injection"),
        ],
    )
    def test_invalid_ticker_returns_422(self, setup_app, ticker):
        client, provider, llm = setup_app()

        response = client.get(f"/news/{ticker}/summary")

        assert response.status_code == 422
        assert provider.requested == []
        assert llm.calls == 0

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/news//summary", id="empty-ticker"),
            pytest.param("/news/AA/PL/summary", id="slash-in-ticker"),
            pytest.param("/news/AAPL", id="missing-suffix"),
            pytest.param("/unknown", id="unknown-route"),
        ],
    )
    def test_unknown_paths_return_404(self, setup_app, path):
        client, _, _ = setup_app()

        assert client.get(path).status_code == 404

    @pytest.mark.parametrize("method", ["post", "put", "delete"])
    def test_wrong_method_returns_405(self, setup_app, method):
        client, _, _ = setup_app()

        response = getattr(client, method)("/news/AAPL/summary")

        assert response.status_code == 405


class TestGetSummaryErrors:
    def test_news_unavailable_returns_503(self, setup_app):
        provider = FakeNewsProvider(error=NewsUnavailableError("AAPL"))
        client, _, llm = setup_app(provider=provider)

        response = client.get("/news/AAPL/summary")

        assert response.status_code == 503
        assert response.json() == {"detail": "News unavailable for AAPL"}
        assert llm.calls == 0

    def test_summary_unavailable_returns_503(self, setup_app):
        client, _, _ = setup_app(llm=FakeLLMClient(error=SummaryUnavailableError()))

        response = client.get("/news/AAPL/summary")

        assert response.status_code == 503
        assert response.json() == {"detail": "Summary unavailable"}

    def test_service_errors_are_logged_once_with_traceback(self, setup_app, caplog):
        provider = FakeNewsProvider(error=NewsUnavailableError("AAPL"))
        client, _, _ = setup_app(provider=provider)

        with caplog.at_level(logging.ERROR, logger="app.main"):
            client.get("/news/AAPL/summary")

        [record] = [r for r in caplog.records if r.name == "app.main"]
        assert "NewsUnavailableError" in record.getMessage()
        assert "/news/AAPL/summary" in record.getMessage()
        assert record.exc_info is not None

    def test_unexpected_errors_return_500(self, setup_app):
        provider = FakeNewsProvider(error=ValueError("bug in our code"))
        client, _, _ = setup_app(provider=provider)

        response = client.get("/news/AAPL/summary")

        assert response.status_code == 500
        assert "bug in our code" not in response.text
