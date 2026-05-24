"""Build the research_metrics dataset from stored sentiment and price data.

This script joins ``news_sentiment`` and ``stock_prices`` to compute
forward returns and abnormal returns for every sentiment observation.

Pipeline
--------
1. Load all sentiment records grouped by (symbol, date).
2. Load stock prices and benchmark prices from the database.
3. For each sentiment date, compute:
   - 1-day, 3-day, 7-day, 30-day future returns
   - 1-day and 7-day abnormal returns (vs Nifty 50)
4. Upsert results into ``research_metrics`` table.

Look-ahead bias prevention
--------------------------
- After-market news is shifted to the next trading day.
- Future returns use only subsequent prices.
- Weekends and holidays are skipped.

Usage
-----
::

    python -m scripts.build_research_dataset    # from backend/
    python scripts/build_research_dataset.py    # direct execution
"""

import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd

_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from scripts.config import BENCHMARK, SYMBOLS, setup_logging
from database import init_db, NewsSentiment, ResearchMetric, StockPrice
from database.database import get_db
from services.data_quality import align_to_market_hours
from services.research_service import build_research_metrics

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_sentiment_dates(db, symbol: str) -> list[tuple[date, float]]:
    """Load and aggregate daily sentiment scores for a symbol.

    Returns a list of (market_aligned_date, avg_sentiment_score) tuples.
    """
    rows = (
        db.query(NewsSentiment)
        .filter(NewsSentiment.symbol == symbol)
        .filter(NewsSentiment.sentiment_score.isnot(None))
        .all()
    )

    if not rows:
        return []

    # Align each headline's publication time to the correct trading day,
    # then average sentiment per trading day.
    daily = {}
    for row in rows:
        trading_date = align_to_market_hours(row.published_at)
        if trading_date not in daily:
            daily[trading_date] = []
        daily[trading_date].append(row.sentiment_score)

    result = []
    for d, scores in sorted(daily.items()):
        avg_score = round(sum(scores) / len(scores), 6)
        result.append((d, avg_score))

    logger.info("Loaded %d sentiment dates for %s", len(result), symbol)
    return result


def load_prices_as_df(db, symbol: str) -> pd.DataFrame:
    """Load stock prices from DB into a pandas DataFrame."""
    rows = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol)
        .order_by(StockPrice.date)
        .all()
    )

    if not rows:
        return pd.DataFrame(columns=["date", "close"])

    data = [{"date": r.date, "close": r.close} for r in rows]
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def store_research_metrics(db, metrics: list[dict]) -> dict:
    """Upsert research metrics into the database.

    Returns insert/skip counts.
    """
    stats = {"inserted": 0, "skipped": 0, "updated": 0}

    for m in metrics:
        existing = (
            db.query(ResearchMetric)
            .filter(
                ResearchMetric.symbol == m["symbol"],
                ResearchMetric.date == m["date"],
            )
            .first()
        )

        if existing:
            # Update with fresh return calculations
            existing.sentiment_score = m["sentiment_score"]
            existing.future_return_1d = m.get("future_return_1d")
            existing.future_return_3d = m.get("future_return_3d")
            existing.future_return_7d = m.get("future_return_7d")
            existing.future_return_30d = m.get("future_return_30d")
            existing.abnormal_return_1d = m.get("abnormal_return_1d")
            existing.abnormal_return_7d = m.get("abnormal_return_7d")
            stats["updated"] += 1
        else:
            row = ResearchMetric(
                symbol=m["symbol"],
                date=m["date"],
                sentiment_score=m["sentiment_score"],
                future_return_1d=m.get("future_return_1d"),
                future_return_3d=m.get("future_return_3d"),
                future_return_7d=m.get("future_return_7d"),
                future_return_30d=m.get("future_return_30d"),
                abnormal_return_1d=m.get("abnormal_return_1d"),
                abnormal_return_7d=m.get("abnormal_return_7d"),
            )
            db.add(row)
            stats["inserted"] += 1

    db.commit()
    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_for_symbol(symbol: str) -> dict:
    """Build research metrics for a single symbol."""
    with get_db() as db:
        sentiment_dates = load_sentiment_dates(db, symbol)
        if not sentiment_dates:
            logger.info("No sentiment data for %s, skipping", symbol)
            return {"symbol": symbol, "sentiment_dates": 0, "inserted": 0, "updated": 0}

        stock_prices_df = load_prices_as_df(db, symbol)
        benchmark_prices_df = load_prices_as_df(db, BENCHMARK)

        if stock_prices_df.empty:
            logger.warning("No price data for %s, skipping", symbol)
            return {"symbol": symbol, "sentiment_dates": len(sentiment_dates), "inserted": 0, "updated": 0}

        if benchmark_prices_df.empty:
            logger.warning(
                "No benchmark (%s) prices — abnormal returns will be NULL", BENCHMARK,
            )

        metrics = build_research_metrics(
            symbol=symbol,
            sentiment_dates=sentiment_dates,
            stock_prices_df=stock_prices_df,
            benchmark_prices_df=benchmark_prices_df,
        )

        result = store_research_metrics(db, metrics)

    return {
        "symbol": symbol,
        "sentiment_dates": len(sentiment_dates),
        **result,
    }


def build_all() -> list[dict]:
    """Build research metrics for all configured symbols."""
    init_db()
    all_stats = []

    for symbol in SYMBOLS:
        logger.info("--- Building research dataset for %s ---", symbol)
        s = build_for_symbol(symbol)
        all_stats.append(s)
        logger.info(
            "%s: %d sentiment dates -> %d inserted, %d updated, %d skipped",
            s["symbol"], s["sentiment_dates"],
            s.get("inserted", 0), s.get("updated", 0), s.get("skipped", 0),
        )

    return all_stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging()
    logger.info("=== Research Dataset Build Started ===")
    results = build_all()

    total_inserted = sum(r.get("inserted", 0) for r in results)
    total_updated = sum(r.get("updated", 0) for r in results)
    logger.info(
        "=== Research Dataset Build Complete: %d inserted, %d updated across %d symbols ===",
        total_inserted, total_updated, len(results),
    )
