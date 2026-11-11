from .news import NewsProvider, YFinanceProvider
from .llmclients import LLMClient, OpenAIClient
from .summarizer import NewsSummarizer
from typing import Annotated
from fastapi import Depends
from .config import Settings, get_settings
from functools import lru_cache


def get_news_provider() -> NewsProvider:
    return YFinanceProvider()


def get_llm_client() -> LLMClient:
    settings = get_settings()
    return OpenAIClient(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_model,
        timeout=settings.openai_timeout,
    )


def get_summarizer(
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> NewsSummarizer:
    return NewsSummarizer(llm)
