import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { ApiError, fetchSummary } from "../src/api";
import { makeSummaryResponse } from "./fixtures";
import type { SummaryResponse } from "../src/types";

vi.mock("../src/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../src/api")>()),
  fetchSummary: vi.fn(),
}));

const fetchSummaryMock = vi.mocked(fetchSummary);

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function pendingRequest(signal?: AbortSignal) {
  const d = deferred<SummaryResponse>();
  signal?.addEventListener("abort", () =>
    d.reject(new DOMException("Aborted", "AbortError")),
  );
  return d;
}

describe("App", () => {
  beforeEach(() => {
    fetchSummaryMock.mockReset();
  });

  it("shows loading, then the summary", async () => {
    const user = userEvent.setup();
    const request = deferred<SummaryResponse>();
    fetchSummaryMock.mockReturnValue(request.promise);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "AAPL" }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Reading the latest news for AAPL",
    );

    request.resolve(makeSummaryResponse());
    expect(
      await screen.findByText("Strong quarter, softer China demand."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows the ApiError message on failure", async () => {
    const user = userEvent.setup();
    fetchSummaryMock.mockRejectedValue(new ApiError(503, "Provider down."));
    render(<App />);

    await user.click(screen.getByRole("button", { name: "MSFT" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load MSFT");
    expect(alert).toHaveTextContent("Provider down.");
  });

  it("shows a generic message for unexpected errors", async () => {
    const user = userEvent.setup();
    fetchSummaryMock.mockRejectedValue(new Error("boom"));
    render(<App />);

    await user.click(screen.getByRole("button", { name: "MSFT" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Something went wrong. Please try again.",
    );
  });

  it("blocks a second search while one is loading", async () => {
    const user = userEvent.setup();
    fetchSummaryMock.mockImplementation(
      (_ticker, signal) => pendingRequest(signal).promise,
    );
    render(<App />);

    const input = screen.getByLabelText("Stock ticker");
    await user.type(input, "aapl{Enter}");
    expect(input).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "MSFT" }));

    expect(fetchSummaryMock).toHaveBeenCalledExactlyOnceWith(
      "AAPL",
      expect.any(AbortSignal),
    );
  });

  it("can search again after a result arrives", async () => {
    const user = userEvent.setup();
    fetchSummaryMock
      .mockResolvedValueOnce(makeSummaryResponse())
      .mockResolvedValueOnce(makeSummaryResponse({ ticker: "TSLA" }));
    render(<App />);

    await user.click(screen.getByRole("button", { name: "AAPL" }));
    await screen.findByText("AAPL", { selector: ".ticker" });
    await user.click(screen.getByRole("button", { name: "TSLA" }));

    expect(
      await screen.findByText("TSLA", { selector: ".ticker" }),
    ).toBeInTheDocument();
    expect(fetchSummaryMock).toHaveBeenCalledTimes(2);
  });

  it("aborts the in-flight request on unmount", async () => {
    const user = userEvent.setup();
    fetchSummaryMock.mockImplementation(
      (_ticker, signal) => pendingRequest(signal).promise,
    );
    const { unmount } = render(<App />);

    await user.click(screen.getByRole("button", { name: "NVDA" }));
    const signal = fetchSummaryMock.mock.calls[0][1];
    unmount();

    expect(signal?.aborted).toBe(true);
  });
});
