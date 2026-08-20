# Noom Nugaom Stock Analyst API

FastAPI backend for a stock-analysis chatbot. It returns price metadata, support/resistance, trend, RSI/MACD/SMA, financial snapshots, and an LLM-ready master prompt. The default is deliberately **free-data-first**, so all market data must be treated as indicative rather than executable trading data.

## What works now

- `GET /v1/analysis/{symbol}` — technical analysis from daily/weekly OHLCV. Thai tickers are mapped to Yahoo Finance's `.BK` suffix.
- `GET /v1/fundamentals/{symbol}` — quarterly fundamental fields from Yahoo Finance via `yfinance`.
- `GET /v1/fundamentals/{symbol}?market=US&provider=sec` — official US SEC EDGAR company facts, after setting `SEC_USER_AGENT`.
- `GET /v1/chat-context/{symbol}` — a master system prompt plus structured analysis for an LLM/chat UI.
- `GET /health` — service liveness check.

## GPT Action and production deployment

The FastAPI schema is exposed at `/openapi.json`. A ready-to-edit Action schema and setup guide live in [`docs/`](docs/). Before public deployment, use a **new** `ACTION_API_KEY`, set `APP_ENV=production`, and configure `PUBLIC_BASE_URL` to the final HTTPS URL. Production startup fails if the action key is missing.

The Action routes use an `X-API-Key` header. Health remains public for the deployment platform. The production secret belongs only in the host's encrypted environment-variable store and the GPT Action authentication setting.

## Data-source policy

| Need | Default source | Status |
| --- | --- | --- |
| Thai and US OHLCV | Yahoo Finance via `yfinance` | Free but unofficial; can be delayed and incomplete |
| US filings | SEC EDGAR `data.sec.gov` | Official, free, requires a descriptive User-Agent |
| Thai filings | SET and SEC Thailand | Recommended verification sources; not mass-scraped by this service |
| GoogleFinance | Google Sheets formula | Suitable for manual spreadsheet use; not used as a backend feed because historical `GOOGLEFINANCE` values cannot be accessed via Sheets API/Apps Script |

Do not use this service to place orders. Confirm price and corporate action data with an exchange, broker, SET, SEC Thailand, or SEC EDGAR filing before making an investment decision.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs>.

```bash
curl 'http://localhost:8000/v1/analysis/PTT?market=TH&period=1y&interval=1d'
curl 'http://localhost:8000/v1/fundamentals/AAPL?market=US&provider=sec'
curl 'http://localhost:8000/v1/chat-context/CPALL?market=TH'
pytest
```

To enable the official SEC adapter, set a transparent contact User-Agent:

```bash
export SEC_USER_AGENT='NoomNugaom/0.1 your-email@example.com'
```

See [`docs/gpt-action-setup.md`](docs/gpt-action-setup.md) after deployment.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

## Production notes

- Replace the in-memory cache with Redis before using multiple replicas.
- Add a licensed real-time market-data provider if this will guide intraday execution.
- Add a Thai filing adapter only after confirming the relevant SET/SEC Thailand access and redistribution terms.
- Put any LLM API key only on the server; never expose it in a browser client.
