import { useState } from "react";

const POPULAR_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"];

interface TickerFormProps {
  onSearch: (ticker: string) => void;
  loading: boolean;
}

export function TickerForm({ onSearch, loading }: TickerFormProps) {
  const [text, setText] = useState("");
  const ticker = text.trim().toUpperCase();

  function pick(suggestion: string) {
    setText(suggestion);
    onSearch(suggestion);
  }

  return (
    <form
      className="search"
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        if (ticker) onSearch(ticker);
      }}
    >
      <label htmlFor="ticker" className="visually-hidden">
        Stock ticker
      </label>
      <div className="search-field">
        <svg className="search-icon" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <input
          id="ticker"
          type="text"
          placeholder="Enter a ticker, e.g. AAPL"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          maxLength={10}
          value={text}
          disabled={loading}
          onChange={(event) => setText(event.target.value)}
        />
        <button type="submit" disabled={loading || !ticker}>
          {loading ? "Loading…" : "Get brief"}
        </button>
      </div>

      <div className="suggestions">
        <span className="suggestions-label">Popular</span>
        {POPULAR_TICKERS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            className="chip"
            disabled={loading}
            onClick={() => pick(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </form>
  );
}
