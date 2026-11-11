import type { Sentiment, SummaryResponse } from "../types";
import { ArticleList } from "./ArticleList";
import { KeyPointList } from "./KeyPointList";

const SENTIMENT_LABELS: Record<Sentiment, string> = {
  bullish: "Bullish",
  bearish: "Bearish",
  neutral: "Neutral",
  mixed: "Mixed",
};

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}


export function SummaryView({ data }: { data: SummaryResponse }) {
  const { ticker, summary, articles, generated_at } = data;

  return (
    <div className="card">
      <div className="card-header">
        <span className="ticker">{ticker}</span>
        <span className="muted">Updated {formatDateTime(generated_at)}</span>
      </div>

      {summary === null ? (
        <p className="empty">
          No recent news found for <strong>{ticker}</strong>. Check the ticker
          or try again later.
        </p>
      ) : (
        <>
          <section className="overview" aria-labelledby="overview-heading">
            <div className="overview-heading">
              <h2 id="overview-heading">Overview</h2>
              <span className={`sentiment sentiment-${summary.sentiment}`}>
                {SENTIMENT_LABELS[summary.sentiment]}
              </span>
            </div>
            <p className="overview-text">{summary.overview}</p>
          </section>

          <KeyPointList keyPoints={summary.key_points} articles={articles} />
        </>
      )}

      {articles.length > 0 && <ArticleList articles={articles} />}
    </div>
  );
}





