# Market Brief

An AI-generated, one-page summary of the latest news for a stock. Enter a ticker (e.g. `AAPL`) to get an overview, the overall sentiment, key points, and links to the source articles.

**Backend:** Python, FastAPI, OpenAI · **Frontend:** React, TypeScript, Vite

## Getting started

### Requirements

- **Python** 3.10+
- **Node.js** 22 LTS+ (includes npm)
- An **OpenAI API key**

### 1. Add your OpenAI API key

```bash
cp backend/.env.example backend/.env     # Windows: Copy-Item backend\.env.example backend\.env
```

Set `OPENAI_API_KEY` in `backend/.env`. `OPENAI_MODEL` is optional. If `OPENAI_API_KEY` is already set in your shell, you can skip this step.

### 2. Start the backend

From the project root:

```bash
python -m venv venv
source venv/bin/activate                 # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Leave this terminal running. The frontend expects the backend on port 8000.

### 3. Start the frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

The app is now running. Open **http://localhost:5173** in your browser, enter a ticker such as `AAPL`, and press **Get brief**. Keep both terminals open while you use it.

### Optional: run the tests

No API key or internet connection needed.

```bash
cd backend && pytest       # with the virtual environment active
cd frontend && npm test
```

## Design decisions

- **Swappable news source and LLM.** `NewsProvider` and `LLMClient` are `Protocol`s, wired together with FastAPI `Depends` in `dependency.py`. Adding another news API or LLM means writing one class. The prompt and business rules live in `prompts.py` and `summarizer.py`, so every provider shares them.
- **Yahoo Finance via `yfinance`.** It needs no API key, so an OpenAI key is all you need. It is unofficial and its data format can change. In production I would use a licensed feed instead, which would be a new `NewsProvider`.
- **Grounded summaries.** The model answers in a fixed JSON schema (OpenAI structured outputs). It cites articles by number, never by URL. The server removes invalid citations and drops any key point with no valid source, and the frontend links each number to the real article.
- **Prompt-injection defense.** Article text goes inside a delimited section that the prompt marks as data. Delimiter tags in article text are stripped, and the ticker is validated before it reaches the prompt.
- **Error handling.** Failures are wrapped in the app's own exceptions, keeping the original cause, and logged once in a single FastAPI handler. If Yahoo or OpenAI is down, the response is a `503` with a readable message. If there's no news, it returns an empty result without calling the LLM.
- **Frontend.** The Vite dev server forwards `/api` to the backend, so no CORS setup is needed. The page state is one typed union (`idle` / `loading` / `success` / `error`). A new search cancels the previous request, so a slow old answer never overwrites a newer one.

### Testing strategy

External systems (Yahoo Finance, the OpenAI SDK, `fetch`) are replaced with fakes at the edges, and everything in between runs for real. That keeps the tests fast and deterministic.

- **Backend (pytest):** news parsing and error wrapping, prompt building and tag stripping, the OpenAI client's error translation, citation filtering, and the endpoint's status codes via FastAPI's `TestClient` with `dependency_overrides`.
- **Frontend (Vitest + React Testing Library):** API error mapping, form behavior, result rendering, and request cancellation.

Not covered: live tests against the real APIs, and measuring summary quality.
