# Stock Research Dashboard

A full-stack quantitative stock research dashboard for NSE equities. The app combines price action, volume, RSI, MACD, custom date filtering, returns, and multi-panel charting in a compact institutional research interface.

## Tech Stack

Frontend:
- Next.js
- React
- TailwindCSS
- Lightweight Charts
- Axios

Backend:
- FastAPI
- yfinance
- pandas
- ta

## Features

Market data:
- Yahoo Finance powered stock data
- NSE stock support through `.NS`
- Preset timeframes: `1D`, `1W`, `1M`, `3M`, `6M`, `1Y`, `5Y`
- Custom start and end date filtering

Charts:
- Candlestick chart mode
- Line chart mode
- Volume histogram overlay
- Hover OHLC and volume readout
- Multi-panel layout for price, RSI, and MACD

Indicators and analytics:
- RSI
- MACD
- MACD signal
- MACD histogram
- Period return and close-to-close change
- Google News RSS sentiment
- FinBERT headline scoring
- Daily sentiment aggregation
- 7 day rolling sentiment average

UI:
- Professional dark and light themes
- Theme persistence
- Responsive layout for desktop and mobile
- Loading, empty, and error states

Security:
- Configurable CORS allowlist
- In-memory IP rate limiting
- Security response headers
- Symbol, timeframe, and date validation
- Sanitized unexpected backend errors

## Project Structure

```txt
StockResearch/
|-- backend/
|   |-- main.py
|   |-- security.py
|   |-- requirements.txt
|   |-- services/
|   |   |-- __init__.py
|   |   `-- stock_data.py
|   `-- venv/
|
|-- frontend/
|   |-- app/
|   |   |-- components/
|   |   |-- hooks/
|   |   |-- lib/
|   |   |-- globals.css
|   |   |-- layout.js
|   |   `-- page.js
|   |-- public/
|   |-- package.json
|   `-- package-lock.json
|
|-- README.md
`-- PROGRESS.md
```

## Running Locally

Backend:

```powershell
cd D:\StockResearch\backend
venv\Scripts\pip install -r requirements.txt
uvicorn main:app --reload
```

The sentiment route requires the backend packages in `requirements.txt`, including `feedparser`, `transformers`, and `torch`. The first sentiment request can take a while because `ProsusAI/finbert` may need to download and initialize.

Frontend:

```powershell
cd D:\StockResearch\frontend
npm run dev
```

Then open:

```txt
http://localhost:3000
```

## Backend Configuration

Optional environment variables:

```powershell
$env:STOCK_API_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
$env:STOCK_API_RATE_LIMIT_PER_MINUTE="120"
```

Defaults are suitable for local development. If you expose the backend to another machine or domain, add that origin explicitly instead of using a wildcard.

### Access From Another Device

CORS defaults to:

```txt
http://localhost:3000,http://127.0.0.1:3000
```

If you open the frontend from another device, for example:

```txt
http://192.168.1.5:3000
```

Start the backend with that origin included:

```powershell
$env:STOCK_API_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.5:3000"
uvicorn main:app --reload
```

## API

Health:

```txt
GET /
```

Stock data:

```txt
GET /stock/{symbol}?timeframe=1Y
GET /stock/{symbol}?timeframe=1Y&start=2024-01-01&end=2024-12-31
```

Sentiment:

```txt
GET /sentiment/{symbol}
```

Notes:
- `symbol` should be the NSE symbol without `.NS`, for example `RELIANCE`.
- Custom dates use `YYYY-MM-DD`.
- The response remains a list of records on success.
- Error responses preserve the existing `{ "error": "..." }` shape.

Sentiment response:

```json
[
  {
    "date": "2025-01-01",
    "avg_sentiment": -0.42,
    "rolling_sentiment": -0.3,
    "article_count": 15
  }
]
```

## Sentiment Pipeline

```txt
Google News RSS
|
v
Headline cleaning
|
v
FinBERT scoring with ProsusAI/finbert
|
v
Daily aggregation
|
v
7 day rolling average
|
v
Frontend sentiment chart
```

Scoring:
- Positive: `+1 * confidence`
- Neutral: `0`
- Negative: `-1 * confidence`

The FinBERT model is loaded globally once on first sentiment request. The first request can be slower because the model may need to download and initialize.
