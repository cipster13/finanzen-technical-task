import pytest
import app.news as news
from app.exception import NewsUnavailableError
from app.models import Article
from app.news import NewsProvider, YFinanceProvider, parse_yfinance_article
import logging


def create_raw_article(**overrides) -> dict:
    content = {
        "title": "Apple beats earnings",
        "summary": "Revenue up 8% year over year.",
        "description": "Longer description.",
        "pubDate": "2026-11-09T14:30:00Z",
        "provider": {"displayName": "Reuters"},
        "clickThroughUrl": {"url": "https://click.example/apple"},
        "canonicalUrl": {"url": "https://canonical.example/apple"},
    }
    content.update(overrides)
    return {"id": "abc", "content": content}


class FakeTicker:
    def __init__(self, news):
        self.news = news


@pytest.fixture
def fake_yfinance(monkeypatch):
    requested = []

    def setup(articles=[], error=None):
        def fake_ticker(ticker):
            requested.append(ticker)
            if error is not None:
                raise error
            return FakeTicker(articles)

        monkeypatch.setattr(news.yfinance, "Ticker", fake_ticker)
        return requested

    return setup


@pytest.fixture(params=["yfinance"])
def working_provider(request, fake_yfinance) -> NewsProvider:
    if request.param == "yfinance":
        fake_yfinance(
            articles=[create_raw_article(), create_raw_article(title="Second article")]
        )
        return YFinanceProvider()


@pytest.fixture(params=["yfinance"])
def broken_provider(request, fake_yfinance) -> NewsProvider:
    if request.param == "yfinance":
        fake_yfinance(error=ConnectionError("network down"))
        return YFinanceProvider()


class TestNewsProviderContract:
    def test_satisfies_the_protocol(self, working_provider):
        assert isinstance(working_provider, NewsProvider)

    def test_fetch_returns_a_list_of_articles(self, working_provider):
        articles = working_provider.fetch("AAPL")

        assert isinstance(articles, list)
        assert len(articles) == 2
        assert all(isinstance(a, Article) for a in articles)

    def test_fetch_raises_news_unavailable_when_source_fails(self, broken_provider):
        with pytest.raises(NewsUnavailableError):
            broken_provider.fetch("AAPL")


class TestYFinanceProvider:
    def test_asks_yfinance_for_the_given_ticker(self, fake_yfinance):
        requested = fake_yfinance(articles=[])

        YFinanceProvider().fetch("TSLA")

        assert requested == ["TSLA"]

    def test_skips_unparseable_articles_and_keeps_the_rest(self, fake_yfinance):
        fake_yfinance(
            articles=[create_raw_article(title="Good"), create_raw_article(title=None)]
        )

        articles = YFinanceProvider().fetch("AAPL")

        assert [a.title for a in articles] == ["Good"]

    def test_no_news_returns_empty_list(self, fake_yfinance):
        fake_yfinance(articles=[])
        assert YFinanceProvider().fetch("AAPL") == []

    def test_original_error_is_kept_as_cause(self, fake_yfinance):
        original = ConnectionError("network down")
        fake_yfinance(error=original)

        with pytest.raises(NewsUnavailableError) as exc_info:
            YFinanceProvider().fetch("AAPL")

        assert exc_info.value.__cause__ is original


class TestParseYFinanceArticle:
    def test_parses_a_complete_article(self):
        article = parse_yfinance_article(create_raw_article())

        assert article.title == "Apple beats earnings"
        assert article.summary == "Revenue up 8% year over year."
        assert article.url == "https://click.example/apple"
        assert article.publisher == "Reuters"
        assert article.published_at.year == 2026

    def test_url_falls_back_to_canonical_url(self):
        article = parse_yfinance_article(create_raw_article(clickThroughUrl=None))
        assert article.url == "https://canonical.example/apple"

    def test_summary_falls_back_to_description(self):
        article = parse_yfinance_article(create_raw_article(summary=None))
        assert article.summary == "Longer description."

    def test_summary_is_none_when_both_missing(self):
        article = parse_yfinance_article(
            create_raw_article(summary="", description=None)
        )
        assert article.summary is None

    def test_publisher_defaults_to_unknown(self):
        article = parse_yfinance_article(create_raw_article(provider=None))
        assert article.publisher == "Unknown"

    @pytest.mark.parametrize(
        "raw",
        [
            pytest.param({}, id="empty-dict"),
            pytest.param({"content": None}, id="content-none"),
            pytest.param(create_raw_article(title=None), id="no-title"),
            pytest.param(
                create_raw_article(clickThroughUrl=None, canonicalUrl=None), id="no-url"
            ),
            pytest.param(create_raw_article(pubDate="not a date"), id="bad-date"),
        ],
    )
    def test_invalid_input_returns_none(self, raw):
        assert parse_yfinance_article(raw) is None

    def test_invalid_input_logs_a_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            parse_yfinance_article(create_raw_article(title=None))

        assert "Error while parsing the article" in caplog.text
