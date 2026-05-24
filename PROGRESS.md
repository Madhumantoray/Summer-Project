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
- Added chart resize handling
- Improved chart lifecycle cleanup
- Removed remote Google font build dependency
- Updated metadata
- Reworked UI toward a compact quantitative research interface

## Current Architecture

```txt
Frontend (Next.js)
    |
    | HTTP
    v
FastAPI Backend
    |
    | yfinance
    v
Yahoo Finance
    |
    v
Indicator Service (pandas + ta)
```

Frontend modules:

```txt
app/page.js
app/components/
app/hooks/
app/lib/
```

Backend modules:

```txt
backend/main.py
backend/security.py
backend/services/stock_data.py
```

## Verified

- Frontend lint passes.
- Frontend production build passes.
- Desktop layout checked in browser.
- Mobile layout checked in browser.
- Backend unavailable state handled gracefully.

## Known Remaining Items

- Recreate or repair the backend virtualenv if the local Python path changes.
- Add backend unit tests for validation, timeframe mapping, indicator columns, and empty data responses.
- Add frontend tests for fetch URL construction, returns calculation, and chart data transforms.
- Replace in-memory rate limiting with Redis or another shared store before multi-process production deployment.
- Tighten allowed CORS origins for any deployed domain.

## Next Phase Ideas

- Add sentiment ingestion.
- Add news source management.
- Add sentiment scoring.
- Add event study views.
- Add watchlists.
- Add exportable research reports.
