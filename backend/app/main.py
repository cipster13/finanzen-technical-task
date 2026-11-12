from fastapi import FastAPI, Depends, Path, Request
from fastapi.responses import JSONResponse
from .summarizer import NewsSummarizer
from .news import NewsProvider
from .models import SummaryResponse
from .exception import ServiceUnavailableError, LLMAuthenticationError
import logging
from .dependency import get_news_provider, get_summarizer
from typing import Annotated
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/news/{ticker}/summary", response_model=SummaryResponse)
def get_summary(
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z0-9.\-]{1,10}$")],
    news_provider: Annotated[NewsProvider, Depends(get_news_provider)],
    summarizer: Annotated[NewsSummarizer, Depends(get_summarizer)],
):
    ticker = ticker.upper()
    articles = news_provider.fetch(ticker)
    summary = summarizer.summarize(ticker, articles)
    return SummaryResponse(
        ticker=ticker,
        summary=summary,
        articles=articles,
        generated_at=datetime.now(timezone.utc),
    )


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    logger.error(
        "%s while handling %s %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.exception_handler(LLMAuthenticationError)
async def llm_authentication_handler(request: Request, exc: LLMAuthenticationError):
    logger.critical(
        "%s while handling %s %s: %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        exc,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Something went wrong. Please try again."},
    )
