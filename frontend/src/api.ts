import type { SummaryResponse } from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function fetchSummary(
  ticker: string,
  signal?: AbortSignal,
): Promise<SummaryResponse> {
  const url = `/api/news/${encodeURIComponent(ticker)}/summary`;

  let response: Response;
  try {
    response = await fetch(url, { signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(0, "Can't reach the server. Is the backend running?");
  }

  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }

  return (await response.json()) as SummaryResponse;
}

async function errorMessage(response: Response): Promise<string> {
  if (response.status === 422) {
    return "That doesn't look like a valid ticker.";
  }
  if (response.status === 503) {
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        return body.detail;
      }
    } catch {
      // Body was not JSON; fall through to the generic message.
    }
  }
  return "Something went wrong. Please try again.";
}
