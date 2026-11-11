from fastapi import FastAPI
from .news import YFinanceProvider
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI()


def get_news():
    return


def main():
    newsProvider = YFinanceProvider()
    articles = newsProvider.fetch("AAPL")
    for i, article in enumerate(articles, start=1):
        print(f"\n--- Article {i} of {len(articles)} ---")
        print(article)


if __name__ == "__main__":
    main()
