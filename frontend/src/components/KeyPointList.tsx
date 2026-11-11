import type { Article, KeyPoint } from "../types";

export function KeyPointList({
  keyPoints,
  articles,
}: {
  keyPoints: KeyPoint[];
  articles: Article[];
}) {
  return (
    <details className="disclosure" open>
      <summary>
        <span>Key points</span>
        <span className="count">{keyPoints.length}</span>
      </summary>
      {keyPoints.length === 0 ? (
        <p className="disclosure-empty">
          No key points could be backed by the articles.
        </p>
      ) : (
        <ul className="key-points">
          {keyPoints.map((point, index) => (
            <li key={index}>
              <span>{point.text}</span>
              <span className="citations">
                {point.sources.map((source) => (
                  <Citation
                    key={source}
                    number={source}
                    article={articles[source - 1]}
                  />
                ))}
              </span>
            </li>
          ))}
        </ul>
      )}
    </details>
  );
}

function Citation({ number, article }: { number: number; article?: Article }) {
  if (!article) {
    return <span className="citation">{number}</span>;
  }
  return (
    <a
      className="citation"
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      title={`${article.publisher}: ${article.title}`}
      aria-label={`Source ${number}: ${article.title}`}
    >
      {number}
    </a>
  );
}