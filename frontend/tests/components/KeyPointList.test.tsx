import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KeyPointList } from "../../src/components/KeyPointList";
import type { KeyPoint } from "../../src/types";
import { makeSummaryResponse } from "../fixtures";

const { articles } = makeSummaryResponse();

function renderList(keyPoints: KeyPoint[]) {
  return render(<KeyPointList keyPoints={keyPoints} articles={articles} />);
}

describe("KeyPointList", () => {
  it("shows every key point and the count", () => {
    renderList([
      { text: "Earnings beat expectations", sources: [1] },
      { text: "China sales are slowing", sources: [2] },
    ]);

    expect(screen.getByText("Earnings beat expectations")).toBeInTheDocument();
    expect(screen.getByText("China sales are slowing")).toBeInTheDocument();
    const header = screen.getByText("Key points").closest("summary")!;
    expect(within(header).getByText("2")).toBeInTheDocument();
  });

  it("is expanded by default", () => {
    const { container } = renderList([{ text: "A point", sources: [1] }]);

    expect(container.querySelector("details")).toHaveAttribute("open");
  });

  it("links a citation to its article (sources are 1-based)", () => {
    renderList([{ text: "A point", sources: [2] }]);

    const citation = screen.getByRole("link", {
      name: "Source 2: iPhone sales slow in China",
    });
    expect(citation).toHaveTextContent("2");
    expect(citation).toHaveAttribute("href", "https://example.com/b");
    expect(citation).toHaveAttribute(
      "title",
      "Bloomberg: iPhone sales slow in China",
    );
    expect(citation).toHaveAttribute("target", "_blank");
    expect(citation).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders one citation per source", () => {
    renderList([{ text: "A point", sources: [1, 2] }]);

    const point = screen.getByText("A point").closest("li")!;
    expect(within(point).getAllByRole("link")).toHaveLength(2);
  });

  it("renders a source with no matching article as plain text", () => {
    renderList([{ text: "Orphan point", sources: [9] }]);

    const point = screen.getByText("Orphan point").closest("li")!;
    expect(within(point).getByText("9")).toBeInTheDocument();
    expect(within(point).queryByRole("link")).not.toBeInTheDocument();
  });

  it("explains when no key point could be backed by a source", () => {
    renderList([]);

    expect(
      screen.getByText("No key points could be backed by the articles."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
