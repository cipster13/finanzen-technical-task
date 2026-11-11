import { useEffect, useRef, useState } from "react";
import { ApiError, fetchSummary } from "./api";
import { SummaryView } from "./components/SummaryView";
import { TickerForm } from "./components/TickerForm";
import type { SearchState } from "./types";
import "./App.css";

function App() {
  const [state, setState] = useState<SearchState>({ status: "idle" });
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => () => controllerRef.current?.abort(), []);

  async function handleSearch(ticker: string) {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setState({ status: "loading", ticker });
    try {
      const data = await fetchSummary(ticker, controller.signal);
      setState({ status: "success", data });
    } catch (error) {
      if (controller.signal.aborted) return;
      const message =
        error instanceof ApiError
          ? error.message
          : "Something went wrong. Please try again.";
      setState({ status: "error", ticker, message });
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <svg className="brand-mark" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3 17l5-5 4 4 8-8" />
              <path d="M15 8h5v5" />
            </svg>
            <span className="brand-name">Market Brief</span>
          </div>
          <span className="badge">AI news summaries</span>
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <h1>What&apos;s moving your stocks?</h1>
          <p className="hero-text">
            Get a one-page brief of the latest news for any ticker, with every
            point linked to its source.
          </p>
          <TickerForm
            onSearch={handleSearch}
            loading={state.status === "loading"}
          />
        </section>

        <section className="results">
          {state.status === "loading" && (
            <div className="card" aria-busy="true">
              <p className="card-status" role="status">
                Reading the latest news for <strong>{state.ticker}</strong>…
              </p>
              <div className="skeleton skeleton-title" />
              <div className="skeleton" />
              <div className="skeleton" />
              <div className="skeleton skeleton-short" />
            </div>
          )}

          {state.status === "error" && (
            <div className="card card-error" role="alert">
              <p className="card-error-title">
                Couldn&apos;t load {state.ticker}
              </p>
              <p>{state.message}</p>
            </div>
          )}

          {state.status === "success" && <SummaryView data={state.data} />}
        </section>
      </main>

      <footer className="footer">
        Summaries are AI-generated from public news and may contain mistakes.
        Not investment advice.
      </footer>
    </div>
  );
}

export default App;
