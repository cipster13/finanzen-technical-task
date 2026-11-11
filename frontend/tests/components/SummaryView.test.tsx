import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SummaryView } from "../../src/components/SummaryView";
import { makeSummaryResponse } from "../fixtures";

describe("SummaryView", () => {
  it("shows the ticker, overview and sentiment", () => {
    render(<SummaryView data={makeSummaryResponse()} />);

    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(
      screen.getByText("Strong quarter, softer China demand."),
    ).toBeInTheDocument();
    expect(screen.getByText("Mixed")).toBeInTheDocument();
  });

  it.each([
    ["bullish", "Bullish"],
    ["bearish", "Bearish"],
    ["neutral", "Neutral"],
    ["mixed", "Mixed"],
  ] as const)("labels %s sentiment as %s", (sentiment, label) => {
    const data = makeSummaryResponse();
    data.summary!.sentiment = sentiment;
    render(<SummaryView data={data} />);

    expect(screen.getByText(label)).toHaveClass(`sentiment-${sentiment}`);
  });

  it("renders both the key points and the articles", () => {
    render(<SummaryView data={makeSummaryResponse()} />);

    expect(screen.getByText("Key points")).toBeInTheDocument();
    expect(screen.getByText("Articles")).toBeInTheDocument();
  });

  it("shows an empty state when there is no summary", () => {
    render(
      <SummaryView
        data={makeSummaryResponse({ summary: null, articles: [] })}
      />,
    );

    expect(screen.getByText(/No recent news found for/)).toBeInTheDocument();
    expect(screen.queryByText("Overview")).not.toBeInTheDocument();
    expect(screen.queryByText("Key points")).not.toBeInTheDocument();
    expect(screen.queryByText("Articles")).not.toBeInTheDocument();
  });

  it("still lists articles when there is no summary", () => {
    render(<SummaryView data={makeSummaryResponse({ summary: null })} />);

    expect(screen.getByText(/No recent news found for/)).toBeInTheDocument();
    expect(screen.getByText("Articles")).toBeInTheDocument();
  });
});
