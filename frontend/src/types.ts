export type Sentiment = "bullish" | "bearish" | "neutral" | "mixed";

export interface Article {
  title: string;
  summary: string | null;
  url: string;
  publisher: string;
  published_at: string;
}

export interface KeyPoint {
  text: string;
  sources: number[];
}

export interface Summary {
  overview: string;
  key_points: KeyPoint[];
  sentiment: Sentiment;
}

export interface SummaryResponse {
  ticker: string;
  summary: Summary | null;
  articles: Article[];
  generated_at: string;
}

export type SearchState =
  | { status: "idle" }
  | { status: "loading"; ticker: string }
  | { status: "success"; data: SummaryResponse }
  | { status: "error"; ticker: string; message: string };
