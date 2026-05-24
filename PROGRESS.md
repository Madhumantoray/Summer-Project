# Stock Research Dashboard Progress

## Project Goal

Build a quantitative stock research platform combining:

- Technical analysis
- Financial data visualization
- NLP-based sentiment analysis
- Behavioral finance research

Core research hypothesis:

> Strongly negative financial sentiment may precede mean-reverting positive returns.

## Current Development Status

## Phase 1: Core Market Dashboard

Status: Completed

### Backend

Completed:
- FastAPI backend
- REST API endpoints
- Yahoo Finance integration through yfinance
- Dynamic stock fetching
- NSE stock handling with `.NS`
- Preset timeframe filtering
- Custom date range filtering
- RSI calculation
- MACD calculation
- MACD signal calculation
- MACD histogram calculation
- Google News RSS sentiment route
- FinBERT headline sentiment service
- Daily sentiment aggregation
- 7 day rolling sentiment average
- Modular stock data service
- Error response shape preserved as `{ "error": "..." }`

Security pass completed:
- In-memory IP rate limiting
- Configurable CORS allowlist
- Basic security headers
- Symbol validation
- Timeframe validation
- ISO date validation
- Sanitized unexpected exceptions

### Frontend

Completed:
- Next.js app
- TailwindCSS styling
- Lightweight Charts integration
- Candlestick chart mode
- Line chart mode
- Volume histogram overlay
- Hover OHLC and volume display
- Period returns panel
- Custom timeframe selection
- Custom date range inputs
- Show button workflow
- Reset dates workflow
- Price, RSI, and MACD panels
- Sentiment chart below MACD
- Daily sentiment line
- Rolling sentiment average line
- Sentiment tooltip
- Sentiment summary card
- Dark and light mode
- Theme persistence
- Theme-aware chart colors
- Loading, empty, and error states
- Responsive desktop and mobile layout

### Refactor Status

Completed:
- Split monolithic frontend page into reusable components
- Moved fetch state into a custom hook
- Moved chart data shaping into shared frontend utilities
- Centralized chart theme tokens
- Added dedicated sentiment data hook
- Added lazy-loaded Recharts sentiment component
- Added chart resize handling
- Improved chart lifecycle cleanup
- Removed remote Google font build dependency
- Updated metadata
- Reworked UI toward a compact quantitative research interface

## Phase 2: Research Infrastructure

Status: Completed

### Database Layer (SQLite + SQLAlchemy)

Completed:
- SQLAlchemy engine with SQLite WAL mode
- Session management with context manager
- Automatic table creation on startup
- `news_sentiment` table with unique constraint on (symbol, headline, published_at)
- `stock_prices` table with unique constraint on (symbol, date)
- `research_metrics` table with unique constraint on (symbol, date)
- Database file at `backend/database/stocks.db`

### Data Quality Module

Completed:
- NSE trading calendar (weekends + holidays 2024-2026)
- `is_trading_day()` and `get_next_trading_day()` functions
- `get_trading_day_offset()` for N-trading-day forward lookups
- Timezone normalization to IST (Asia/Kolkata)
- After-hours alignment: news after 15:30 IST → next trading day
- Headline deduplication via normalized MD5 fingerprints
- Missing price value handling (forward fill / drop / interpolate)

### News Collection Script

Completed:
- Google News RSS as primary source (reuses existing `news_service`)
- yfinance `Ticker.news` as fallback source
- Headline deduplication before storage
- FinBERT sentiment scoring (reuses existing `finbert_service`)
- Upsert into `news_sentiment` table
- Safe re-run: duplicate headlines silently skipped
- Per-symbol collection statistics logging

### Stock Data Collection Script

Completed:
- yfinance OHLCV download with configurable history period (5 years)
- RSI, MACD, MACD signal, MACD histogram computation
- Benchmark index (^NSEI) collection for abnormal returns
- Upsert into `stock_prices` table
- Safe re-run: existing dates silently skipped

### Research Service

Completed:
- Future return computation: 1d, 3d, 7d, 30d windows
- Abnormal return computation: stock return − benchmark return
- `get_next_trading_day()` and `get_trading_day_offset()` for date alignment
- After-market news alignment to prevent look-ahead bias
- Weekend and holiday handling
- Batch computation for all sentiment dates per symbol

### Research Dataset Builder

Completed:
- Joins `news_sentiment` and `stock_prices` tables
- Aggregates daily sentiment per trading day
- Computes forward returns for each sentiment observation
- Computes abnormal returns vs Nifty 50 benchmark
- Upsert into `research_metrics` (insert or update)

### Daily Automated Pipeline

Completed:
- `run_daily_pipeline.py` orchestrator
- Three-step pipeline: news → prices → research metrics
- Per-step timing and error isolation
- Summary statistics at completion
- Exit code reflects success/failure
- Scheduler examples: Windows Task Scheduler, Linux cron, Python `schedule`

### Research Notebooks

Completed:
- `correlation_analysis.py` — Jupytext-compatible research notebook
  - Pearson and Spearman correlations
  - Correlation heatmap
  - Scatter plots (sentiment vs returns, colored by symbol)
  - Rolling sentiment charts (30-day moving average)
  - Return distributions by sentiment tercile
  - Per-symbol correlation breakdown
- `event_study.py` — Jupytext-compatible research notebook
  - Event classification: Strong Negative (<-0.7), Neutral, Strong Positive (>0.7)
  - Group statistics: mean returns, volatility, observation counts
  - Box plots by sentiment group
  - Mean return comparison with error bars
  - Cumulative return plots over event windows
  - Cumulative abnormal return (CAR) plots
  - Welch's t-tests, Mann-Whitney U tests
  - Cohen's d effect sizes
  - 95% confidence intervals

### API Extensions

Completed:
- `GET /research/metrics/{symbol}` — Return forward/abnormal returns from DB
- `GET /research/correlation` — Pearson/Spearman correlation summary
- `GET /research/pipeline/status` — Record counts per table
- Database initialization via FastAPI lifespan handler

### Stock Universe

Configured symbols:
- RELIANCE.NS
- TCS.NS
- INFY.NS
- HDFCBANK.NS
- ICICIBANK.NS

Benchmark: ^NSEI (Nifty 50)

## Current Architecture

```txt
Frontend (Next.js)
    |
    | HTTP
    v
FastAPI Backend
    |
    ├── yfinance → Yahoo Finance
    ├── feedparser → Google News RSS
    ├── transformers → FinBERT (ProsusAI/finbert)
    ├── SQLAlchemy → SQLite (stocks.db)
    |
    v
Indicator Service (pandas + ta)
Research Service (scipy + statsmodels)
```

Backend modules:

```txt
backend/
├── main.py                           # FastAPI app + routes
├── security.py                       # CORS, rate limiting, headers
├── database/
│   ├── __init__.py                   # Package exports
│   ├── database.py                   # Engine, session, init_db
│   └── models.py                     # SQLAlchemy ORM models
├── services/
│   ├── __init__.py
│   ├── stock_data.py                 # yfinance + indicator computation
│   ├── news_service.py               # Google News RSS fetching
│   ├── cleaning_service.py           # Headline cleaning
│   ├── finbert_service.py            # FinBERT sentiment pipeline
│   ├── aggregation_service.py        # Daily sentiment aggregation
│   ├── sentiment_service.py          # Sentiment orchestration
│   ├── research_service.py           # Forward/abnormal return computation
│   └── data_quality.py               # Calendar, timezone, dedup utilities
├── scripts/
│   ├── __init__.py
│   ├── config.py                     # Symbols, benchmark, logging
│   ├── collect_news.py               # News collection + FinBERT scoring
│   ├── collect_stock_data.py         # OHLCV + indicator download
│   ├── build_research_dataset.py     # Forward return computation
│   ├── run_daily_pipeline.py         # Pipeline orchestrator
│   └── scheduler_examples.md         # Cron / Task Scheduler examples
└── research/
    ├── correlation_analysis.py       # Correlation notebook (Jupytext)
    └── event_study.py                # Event study notebook (Jupytext)
```

Frontend modules:

```txt
frontend/
├── app/
│   ├── page.js
│   ├── components/
│   ├── hooks/
│   └── lib/
├── package.json
└── next.config.mjs
```

## Verified

- Frontend lint passes.
- Frontend production build passes.
- Desktop layout checked in browser.
- Mobile layout checked in browser.
- Backend unavailable state handled gracefully.
- Database tables create successfully (3 tables, all columns verified).
- Existing `/stock/{symbol}` and `/sentiment/{symbol}` endpoints unchanged.

## Known Remaining Items

- Recreate or repair the backend virtualenv if the local Python path changes.
- Add backend unit tests for validation, timeframe mapping, indicator columns, and empty data responses.
- Add frontend tests for fetch URL construction, returns calculation, and chart data transforms.
- Replace in-memory rate limiting with Redis or another shared store before multi-process production deployment.
- Tighten allowed CORS origins for any deployed domain.

## Next Phase Ideas

- Add frontend research dashboard views (correlation charts, event study results).
- Add watchlists.
- Add exportable research reports (PDF / HTML).
- Migrate from SQLite to PostgreSQL for concurrent access.
- Add more stock symbols and international markets.
- Add alternative sentiment sources (Twitter, Reddit, news APIs).
