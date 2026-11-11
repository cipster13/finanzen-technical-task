from datetime import datetime, timezone

import pytest

from app.exception import SummaryUnavailableError
from app.models import Article, KeyPoint, Summary
from app.prompts import SYSTEM_PROMPT
from app.summarizer import NewsSummarizer


def create_article(title: str = "Apple beats earnings") -> Article:
    return Article(
        title=title,
        summary="Revenue up 8% year over year.",
        url=f"https://example.com/{title.replace(' ', '-').lower()}",
        publisher="Reuters",
        published_at=datetime(2026, 11, 9, 14, 30, tzinfo=timezone.utc),
    )


def create_summary(*key_points: KeyPoint) -> Summary:
    return Summary(
        overview="Apple had a strong week.",
        key_points=list(key_points),
        sentiment="bullish",
    )


class FakeLLMClient:
    def __init__(self, result: Summary | None = None, error: Exception | None = None):
        self._result = result
        self._error = error
        self.calls = []

    def complete(self, system, user, response_model):
        self.calls.append(
            {"system": system, "user": user, "response_model": response_model}
        )
        if self._error is not None:
            raise self._error
        return self._result


@pytest.fixture
def two_articles() -> list[Article]:
    return [create_article("First story"), create_article("Second story")]


class TestSummarizeSucceed:
    def test_returns_the_llm_summary(self, two_articles):
        llm = FakeLLMClient(result=create_summary(KeyPoint(text="Up", sources=[1])))

        summary = NewsSummarizer(llm).summarize("AAPL", two_articles)

        assert summary.overview == "Apple had a strong week."
        assert summary.sentiment == "bullish"
        assert summary.key_points == [KeyPoint(text="Up", sources=[1])]

    def test_asks_the_llm_for_a_summary(self, two_articles):
        llm = FakeLLMClient(result=create_summary())

        NewsSummarizer(llm).summarize("AAPL", two_articles)

        [call] = llm.calls
        assert call["system"] == SYSTEM_PROMPT
        assert call["response_model"] is Summary

    def test_sends_the_ticker_and_every_article_to_the_llm(self, two_articles):
        llm = FakeLLMClient(result=create_summary())

        NewsSummarizer(llm).summarize("AAPL", two_articles)

        [call] = llm.calls
        assert "AAPL" in call["user"]
        assert "First story" in call["user"]
        assert "Second story" in call["user"]


class TestNoArticles:
    def test_returns_none(self):
        assert NewsSummarizer(FakeLLMClient()).summarize("AAPL", []) is None

    def test_does_not_call_the_llm(self):
        llm = FakeLLMClient()

        NewsSummarizer(llm).summarize("AAPL", [])

        assert llm.calls == []


class TestCitations:
    def summarize_with(self, articles, *key_points: KeyPoint) -> Summary:
        llm = FakeLLMClient(result=create_summary(*key_points))
        return NewsSummarizer(llm).summarize("AAPL", articles)

    def test_valid_sources_are_kept(self, two_articles):
        summary = self.summarize_with(two_articles, KeyPoint(text="A", sources=[1, 2]))

        assert summary.key_points == [KeyPoint(text="A", sources=[1, 2])]

    @pytest.mark.parametrize(
        "bad_source",
        [
            pytest.param(0, id="zero"),
            pytest.param(-1, id="negative"),
            pytest.param(3, id="one-past-the-end"),
            pytest.param(99, id="far-out-of-range"),
        ],
    )
    def test_out_of_range_sources_are_removed(self, two_articles, bad_source):
        summary = self.summarize_with(
            two_articles, KeyPoint(text="A", sources=[1, bad_source])
        )

        assert summary.key_points == [KeyPoint(text="A", sources=[1])]

    def test_duplicate_sources_are_removed_and_sorted(self, two_articles):
        summary = self.summarize_with(
            two_articles, KeyPoint(text="A", sources=[2, 1, 2])
        )

        assert summary.key_points[0].sources == [1, 2]

    @pytest.mark.parametrize(
        "sources",
        [pytest.param([], id="no-sources"), pytest.param([7, 8], id="all-invalid")],
    )
    def test_key_point_without_valid_sources_is_dropped(self, two_articles, sources):
        summary = self.summarize_with(
            two_articles,
            KeyPoint(text="Grounded", sources=[1]),
            KeyPoint(text="Made up", sources=sources),
        )

        assert [p.text for p in summary.key_points] == ["Grounded"]

    def test_key_point_order_is_kept(self, two_articles):
        summary = self.summarize_with(
            two_articles,
            KeyPoint(text="First", sources=[2]),
            KeyPoint(text="Second", sources=[1]),
        )

        assert [p.text for p in summary.key_points] == ["First", "Second"]

    def test_overview_and_sentiment_are_untouched(self, two_articles):
        summary = self.summarize_with(two_articles, KeyPoint(text="A", sources=[9]))

        assert summary.overview == "Apple had a strong week."
        assert summary.sentiment == "bullish"


class TestErrors:
    def test_llm_errors_are_passed_through(self, two_articles):
        error = SummaryUnavailableError()
        llm = FakeLLMClient(error=error)

        with pytest.raises(SummaryUnavailableError) as exc_info:
            NewsSummarizer(llm).summarize("AAPL", two_articles)

        assert exc_info.value is error
