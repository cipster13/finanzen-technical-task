import type { SummaryResponse } from "../src/types";

export function makeSummaryResponse(
  overrides: Partial<SummaryResponse> = {},
): SummaryResponse {
  return {
    ticker: "AAPL",
    generated_at: "2026-11-11T09:30:00Z",
    articles: [
      {
        title: "Apple beats earnings",
        summary: "Revenue up 8%.",
        url: "https://example.com/a",
        publisher: "Reuters",
        published_at: "2026-11-10T14:00:00Z",
      },
      {
        title: "iPhone sales slow in China",
        summary: null,
        url: "https://example.com/b",
        publisher: "Bloomberg",
        published_at: "2026-11-10T16:00:00Z",
      },
    ],
    summary: {
      overview: "Strong quarter, softer China demand.",
      sentiment: "mixed",
      key_points: [
        { text: "Earnings beat expectations", sources: [1] },
        { text: "China sales are slowing", sources: [2] },
      ],
    },
    ...overrides,
  };
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
