"""Collect historical stock price data and technical indicators into the database.

Downloads daily OHLCV from Yahoo Finance via yfinance, computes RSI and
MACD indicators using the existing ``stock_data`` service, and upserts
into the ``stock_prices`` table.

The benchmark index (^NSEI / Nifty 50) is also collected so that
abnormal returns can be computed later in ``build_research_dataset.py``.

Usage
-----
::

    python -m scripts.collect_stock_data    # from backend/
    python scripts/collect_stock_data.py    # direct execution
"""

import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD as MACDIndicator

_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from scripts.config import BENCHMARK, HISTORY_PERIOD, SYMBOLS, setup_logging
from database import init_db, StockPrice
from database.database import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Price download & indicator computation
# ---------------------------------------------------------------------------

def download_prices(symbol: str, period: str = HISTORY_PERIOD) -> pd.DataFrame:
    """Download daily OHLCV from Yahoo Finance.

    Returns a DataFrame with columns:
    ``date, open, high, low, close, volume``
    """
    logger.info("Downloading %s price history (period=%s)", symbol, period)
    df = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        logger.warning("No price data returned for %s", symbol)
        return pd.DataFrame()

    df = df.copy()
    df.reset_index(inplace=True)

    # Flatten multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    # Normalise column names
    df.rename(columns={
        df.columns[0]: "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }, inplace=True)

    # Ensure lowercase
    df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]

    # Convert date to Python date
    df["date"] = pd.to_datetime(df["date"]).dt.date

    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute RSI, MACD, MACD signal, and MACD histogram.

    Replicates the logic from ``services.stock_data.add_indicators``
    but operates on lowercase column names used by the collection pipeline.
    """
    if df.empty or "close" not in df.columns:
        return df

    result = df.copy()

    rsi = RSIIndicator(close=result["close"])
    result["rsi"] = rsi.rsi().fillna(0)

    macd = MACDIndicator(close=result["close"])
    result["macd"] = macd.macd().fillna(0)
    result["macd_signal"] = macd.macd_signal().fillna(0)
    result["macd_histogram"] = macd.macd_diff().fillna(0)

    return result


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------

def store_prices(symbol: str, df: pd.DataFrame) -> dict:
    """Store price rows into the ``stock_prices`` table.

    Existing rows (same symbol + date) are silently skipped via the
    unique constraint, making this safe for repeated runs.

    Returns a dict with ``inserted`` and ``skipped`` counts.
    """
    stats = {"inserted": 0, "skipped": 0}

    with get_db() as db:
        for _, row in df.iterrows():
            try:
                price = StockPrice(
                    symbol=symbol,
                    date=row["date"],
                    open=float(row.get("open", 0) or 0),
                    high=float(row.get("high", 0) or 0),
                    low=float(row.get("low", 0) or 0),
                    close=float(row.get("close", 0) or 0),
                    volume=int(row.get("volume", 0) or 0),
                    rsi=float(row.get("rsi", 0) or 0),
                    macd=float(row.get("macd", 0) or 0),
                    macd_signal=float(row.get("macd_signal", 0) or 0),
                    macd_histogram=float(row.get("macd_histogram", 0) or 0),
                )
                db.add(price)
                db.flush()
                stats["inserted"] += 1
            except Exception:
                db.rollback()
                stats["skipped"] += 1

        db.commit()

    return stats


# ---------------------------------------------------------------------------
# Main collection
# ---------------------------------------------------------------------------

def collect_for_symbol(symbol: str) -> dict:
    """Download, compute indicators, and store prices for one symbol."""
    df = download_prices(symbol)
    if df.empty:
        return {"symbol": symbol, "rows": 0, "inserted": 0, "skipped": 0}

    df = add_indicators(df)
    result = store_prices(symbol, df)

    return {
        "symbol": symbol,
        "rows": len(df),
        "inserted": result["inserted"],
        "skipped": result["skipped"],
    }


def collect_all() -> list[dict]:
    """Collect stock prices for all configured symbols plus the benchmark."""
    init_db()
    all_stats = []
    all_symbols = SYMBOLS + [BENCHMARK]

    for symbol in all_symbols:
        logger.info("--- Collecting prices for %s ---", symbol)
        s = collect_for_symbol(symbol)
        all_stats.append(s)
        logger.info(
            "%s: %d rows downloaded, %d inserted, %d skipped",
            s["symbol"], s["rows"], s["inserted"], s["skipped"],
        )

    return all_stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging()
    logger.info("=== Stock Data Collection Started ===")
    results = collect_all()

    total_inserted = sum(r["inserted"] for r in results)
    total_rows = sum(r["rows"] for r in results)
    logger.info(
        "=== Stock Data Collection Complete: %d/%d rows inserted across %d symbols ===",
        total_inserted, total_rows, len(results),
    )
