from .llmclients import LLMClient
from .models import Article, KeyPoint, Summary
from .prompts import SYSTEM_PROMPT, build_user_prompt
import logging

logger = logging.getLogger(__name__)


class NewsSummarizer:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def summarize(self, ticker: str, articles: list[Article]) -> Summary | None:
        if not articles:
            logger.info("No articles provided to the LLM")
            return None

        summary = self._llm.complete(
            system=SYSTEM_PROMPT,
            user=build_user_prompt(ticker, articles),
            response_model=Summary,
        )
        return _keep_valid_citations(summary, article_count=len(articles))


def _keep_valid_citations(summary: Summary, article_count: int) -> Summary:
    key_points = []
    for point in summary.key_points:
        sources = sorted({s for s in point.sources if 1 <= s <= article_count})
        if sources:
            key_points.append(KeyPoint(text=point.text, sources=sources))
    return summary.model_copy(update={"key_points": key_points})
