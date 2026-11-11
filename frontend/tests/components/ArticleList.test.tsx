import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ArticleList } from "../../src/components/ArticleList";
import { makeSummaryResponse } from "../fixtures";

const { articles } = makeSummaryResponse();

describe("ArticleList", () => {
  it("shows the article count", () => {
    render(<ArticleList articles={articles} />);

    const header = screen.getByText("Articles").closest("summary")!;
    expect(within(header).getByText("2")).toBeInTheDocument();
  });

  it("is collapsed by default", () => {
    const { container } = render(<ArticleList articles={articles} />);

    expect(container.querySelector("details")).not.toHaveAttribute("open");
  });

  it("numbers the articles in order, matching the citation numbers", () => {
    render(<ArticleList articles={articles} />);

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(within(items[0]).getByText("1")).toBeInTheDocument();
    expect(items[0]).toHaveTextContent("Apple beats earnings");
    expect(within(items[1]).getByText("2")).toBeInTheDocument();
    expect(items[1]).toHaveTextContent("iPhone sales slow in China");
  });

  it("links each title to the article in a new tab", () => {
    render(<ArticleList articles={articles} />);

    const link = screen.getByRole("link", { name: "Apple beats earnings" });
    expect(link).toHaveAttribute("href", "https://example.com/a");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("shows the publisher", () => {
    render(<ArticleList articles={articles} />);

    expect(screen.getByText(/^Reuters · /)).toBeInTheDocument();
    expect(screen.getByText(/^Bloomberg · /)).toBeInTheDocument();
  });

  it("shows the article summary only when there is one", () => {
    render(<ArticleList articles={articles} />);

    const [withSummary, withoutSummary] = screen.getAllByRole("listitem");
    expect(within(withSummary).getByText("Revenue up 8%.")).toBeInTheDocument();
    expect(
      withoutSummary.querySelector(".article-summary"),
    ).not.toBeInTheDocument();
  });
});
