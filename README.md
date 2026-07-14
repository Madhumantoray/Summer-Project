# Stock Research Dashboard

A full-stack quantitative stock research platform for NSE equities. Combines price action, volume, technical indicators, NLP-based sentiment analysis, and behavioral finance research infrastructure.

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
- pandas + ta (technical indicators)
- SQLAlchemy + SQLite
- FinBERT (ProsusAI/finbert via Hugging Face transformers)
- feedparser (Google News RSS)

Research:
- scipy
- statsmodels
- matplotlib
- plotly
- Jupytext

## Features

### Market Data
- Yahoo Finance powered stock data
- NSE stock support through `.NS`
- Preset timeframes: `1D`, `1W`, `1M`, `3M`, `6M`, `1Y`, `5Y`
- Custom start and end date filtering

### Charts
- Candlestick chart mode
- Line chart mode
- Volume histogram overlay
- Hover OHLC and volume readout
- Multi-panel layout for price, RSI, and MACD

### Indicators and Analytics
- RSI
- MACD, MACD signal, MACD histogram
- Period return and close-to-close change
- Google News RSS sentiment
- FinBERT headline scoring
- Daily sentiment aggregation
- 7-day rolling sentiment average

### Research Infrastructure
- SQLite database with SQLAlchemy ORM
- Historical news sentiment storage
- Historical stock price storage with technical indicators
- Forward return computation (1d, 3d, 7d, 30d)
- Abnormal returns vs Nifty 50 benchmark
- Automated daily data collection pipeline
- Correlation analysis notebook
- Event study notebook with statistical testing

### UI
- Professional dark and light themes
- Theme persistence
- Responsive layout for desktop and mobile
- Loading, empty, and error states

### Security
- Configurable CORS allowlist
- In-memory IP rate limiting
- Security response headers
- Symbol, timeframe, and date validation
- Sanitized unexpected backend errors

## Project Structure

```txt
StockResearch/
├── backend/
│   ├── main.py                           # FastAPI app + API routes
│   ├── security.py                       # CORS, rate limiting, headers
│   ├── requirements.txt
│   │
│   ├── database/
│   │   ├── __init__.py                   # Package exports
│   │   ├── database.py                   # Engine, session, init_db
│   │   ├── models.py                     # SQLAlchemy ORM models
│   │   └── stocks.db                     # SQLite database (auto-created)
│   │
│   ├── services/
│   │   ├── stock_data.py                 # yfinance + indicators
│   │   ├── news_service.py               # Google News RSS
│   │   ├── cleaning_service.py           # Headline cleaning
│   │   ├── finbert_service.py            # FinBERT sentiment
│   │   ├── aggregation_service.py        # Daily sentiment aggregation
│   │   ├── sentiment_service.py          # Sentiment orchestration
│   │   ├── research_service.py           # Forward/abnormal returns
│   │   └── data_quality.py              # Calendar, timezone, dedup
│   │
│   ├── scripts/
│   │   ├── config.py                     # Symbols, benchmark config
│   │   ├── collect_news.py               # News collection + scoring
│   │   ├── collect_stock_data.py         # OHLCV + indicators
│   │   ├── build_research_dataset.py     # Forward return builder
│   │   ├── run_daily_pipeline.py         # Pipeline orchestrator
│   │   └── scheduler_examples.md         # Scheduling docs
│   │
│   ├── research/
│   │   ├── correlation_analysis.py       # Correlation notebook
│   │   └── event_study.py                # Event study notebook
│   │
│   └── venv/
│
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── globals.css
│   │   ├── layout.js
│   │   └── page.js
│   ├── public/
│   ├── package.json
│   └── package-lock.json
│
├── README.md
└── PROGRESS.md
```

## Running Locally

### Backend

1. Open your terminal and navigate to the backend folder:
   ```powershell
   cd backend
   ```
2. Create and activate a virtual environment (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start the server:
   ```powershell
   python -m uvicorn main:app --reload
   ```

The first sentiment request may be slow because `ProsusAI/finbert` needs to download and initialise (~440MB).

### Frontend

1. Open a new terminal and navigate to the frontend folder:
   ```powershell
   cd frontend
   ```
2. Install dependencies (Node.js required):
   ```powershell
   npm install
   ```
3. Start the development server:
   ```powershell
   npm run dev
   ```

Then open: http://localhost:3000

## Database Setup

The SQLite database is created automatically when the backend starts (via the FastAPI lifespan handler). No manual setup required.

Tables:
- **news_sentiment** — Headlines with FinBERT scores
- **stock_prices** — Daily OHLCV with RSI and MACD
- **research_metrics** — Forward returns and abnormal returns

Database file: `backend/database/stocks.db`

To reset the database, simply delete `stocks.db` and restart the backend.

## Daily Pipeline

The pipeline collects news, fetches prices, and computes research metrics:

```powershell
cd backend
python -m scripts.run_daily_pipeline
```

Pipeline steps:
1. **Fetch news** — Google News RSS + yfinance fallback
2. **Analyze sentiment** — FinBERT scoring
3. **Store sentiment** — Insert into `news_sentiment`
4. **Fetch stock prices** — OHLCV from yfinance
5. **Calculate indicators** — RSI, MACD
6. **Store prices** — Insert into `stock_prices`
7. **Build research metrics** — Forward returns + abnormal returns

You can also run individual steps:

```powershell
venv\Scripts\python scripts\collect_news.py
venv\Scripts\python scripts\collect_stock_data.py
venv\Scripts\python scripts\build_research_dataset.py
```

### Scheduling

See `backend/scripts/scheduler_examples.md` for:
- Windows Task Scheduler XML
- Linux cron job
- Python `schedule` library

Recommended: run daily at 16:30 IST (after NSE market close).

## Research Notebooks

Research notebooks are Jupytext-compatible `.py` files in `backend/research/`.

### Option 1: Run as Python scripts

```powershell
cd D:\StockResearch\backend
venv\Scripts\python research\correlation_analysis.py
venv\Scripts\python research\event_study.py
```

### Option 2: Open in Jupyter

```powershell
cd D:\StockResearch\backend
venv\Scripts\pip install jupyter
venv\Scripts\jupytext --to notebook research\correlation_analysis.py
venv\Scripts\jupytext --to notebook research\event_study.py
venv\Scripts\jupyter notebook research\
```

### Correlation Analysis

Analyses the relationship between FinBERT sentiment and future returns:
- Pearson and Spearman correlations
- Correlation heatmap
- Scatter plots by symbol
- Rolling sentiment charts
- Return distributions by sentiment tercile

### Event Study

Tests the core behavioral finance hypothesis:
- Event classification (strong negative / neutral / strong positive)
- Box plots and mean return comparisons
- Cumulative abnormal return (CAR) plots
- Welch's t-tests, Mann-Whitney U tests
- Cohen's d effect sizes and 95% confidence intervals

## Research Methodology

### Sentiment Scoring

```txt
Google News RSS → Headline cleaning → FinBERT scoring → Daily aggregation
```

Scoring:
- Positive: `+1 × confidence`
- Neutral: `0`
- Negative: `−1 × confidence`

### Forward Returns

```
future_return_N = (P_{t+N} - P_t) / P_t
```

Computed for N = 1, 3, 7, 30 trading days.

### Abnormal Returns

```
abnormal_return = stock_return − benchmark_return
```

Benchmark: Nifty 50 (^NSEI)

### Look-Ahead Bias Prevention

- After-market news (published after 15:30 IST) is attributed to the next trading day
- Forward returns use only subsequent prices
- Weekends and NSE holidays are skipped in trading-day offsets

### Stock Universe

| Symbol | Company |
|--------|---------|
| RELIANCE.NS | Reliance Industries |
| TCS.NS | Tata Consultancy Services |
| INFY.NS | Infosys |
| HDFCBANK.NS | HDFC Bank |
| ICICIBANK.NS | ICICI Bank |

## API

### Existing Endpoints

Health:
```
GET /
```

Stock data:
```
GET /stock/{symbol}?timeframe=1Y
GET /stock/{symbol}?timeframe=1Y&start=2024-01-01&end=2024-12-31
```

Sentiment:
```
GET /sentiment/{symbol}
```

### Research Endpoints (New)

Research metrics:
```
GET /research/metrics/{symbol}
```

Correlation summary:
```
GET /research/correlation
```

Pipeline status:
```
GET /research/pipeline/status
```

Notes:
- `symbol` should be the NSE symbol without `.NS`, for example `RELIANCE`.
- Custom dates use `YYYY-MM-DD`.
- Success responses are lists of records.
- Error responses use `{ "error": "..." }` shape.

## Backend Configuration

Optional environment variables:

```powershell
$env:STOCK_API_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
$env:STOCK_API_RATE_LIMIT_PER_MINUTE="120"
$env:STOCK_DB_URL="sqlite:///D:/StockResearch/backend/database/stocks.db"
```

Defaults are suitable for local development.
