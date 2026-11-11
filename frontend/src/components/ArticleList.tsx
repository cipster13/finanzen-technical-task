import type { Article } from "../types";
import { formatDateTime } from "./SummaryView";


export function ArticleList({ articles }: { articles: Article[] }) {
  return (
    <details className="disclosure">
      <summary>
        <span>Articles</span>
        <span className="count">{articles.length}</span>
      </summary>
      <ol className="articles">
        {articles.map((article, index) => (
          <li key={article.url}>
            <span className="article-number" aria-hidden="true">
              {index + 1}
            </span>
            <div className="article-body">
              <a
                className="article-title"
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {article.title}
              </a>
              <p className="article-meta">
                {article.publisher} · {formatDateTime(article.published_at)}
              </p>
              {article.summary && (
                <p className="article-summary">{article.summary}</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </details>
  );
}