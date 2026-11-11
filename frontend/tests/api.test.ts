import { describe, expect, it, vi } from "vitest";
import { ApiError, fetchSummary } from "../src/api";
import { jsonResponse, makeSummaryResponse } from "./fixtures";

function stubFetch(impl: () => Promise<Response>) {
  const fetchMock = vi.fn(impl);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("fetchSummary", () => {
  it("returns the parsed summary on success", async () => {
    const body = makeSummaryResponse();
    stubFetch(async () => jsonResponse(body));

    await expect(fetchSummary("AAPL")).resolves.toEqual(body);
  });

  it("calls the proxied URL, encodes the ticker and forwards the signal", async () => {
    const fetchMock = stubFetch(async () => jsonResponse(makeSummaryResponse()));
    const controller = new AbortController();

    await fetchSummary("BRK/B", controller.signal);

    expect(fetchMock).toHaveBeenCalledWith("/api/news/BRK%2FB/summary", {
      signal: controller.signal,
    });
  });

  it("maps 422 to a friendly invalid-ticker message", async () => {
    stubFetch(async () => jsonResponse({ detail: [] }, 422));

    await expect(fetchSummary("???")).rejects.toMatchObject({
      name: "ApiError",
      status: 422,
      message: "That doesn't look like a valid ticker.",
    });
  });

  it("uses the backend detail on 503", async () => {
    stubFetch(async () =>
      jsonResponse({ detail: "News provider is down." }, 503),
    );

    await expect(fetchSummary("AAPL")).rejects.toMatchObject({
      status: 503,
      message: "News provider is down.",
    });
  });

  it("falls back to a generic message when a 503 body is not JSON", async () => {
    stubFetch(async () => new Response("<html>oops</html>", { status: 503 }));

    await expect(fetchSummary("AAPL")).rejects.toMatchObject({
      status: 503,
      message: "Something went wrong. Please try again.",
    });
  });

  it("uses a generic message for other errors", async () => {
    stubFetch(async () => jsonResponse({}, 500));

    await expect(fetchSummary("AAPL")).rejects.toMatchObject({
      status: 500,
      message: "Something went wrong. Please try again.",
    });
  });

  it("reports a network failure as status 0", async () => {
    stubFetch(async () => {
      throw new TypeError("Failed to fetch");
    });

    const error = await fetchSummary("AAPL").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 0,
      message: "Can't reach the server. Is the backend running?",
    });
  });

  it("re-throws an abort untouched instead of wrapping it", async () => {
    stubFetch(async () => {
      throw new DOMException("Aborted", "AbortError");
    });

    const error = await fetchSummary("AAPL").catch((e: unknown) => e);

    expect(error).not.toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ name: "AbortError" });
  });
});
