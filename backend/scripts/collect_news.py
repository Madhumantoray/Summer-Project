"""Collect news headlines and FinBERT sentiment scores into the database.

Data sources
------------
1. **Google News RSS** (primary) — fetches recent headlines matching
   ``"{symbol} stock NSE"`` via the existing ``news_service``.
2. **yfinance Ticker.news** (fallback) — attempts to pull headlines
   from Yahoo Finance.  This API is unreliable for NSE stocks and may
   return empty results, so it degrades gracefully.

Pipeline
--------
For each symbol in the configured universe:

1. Fetch raw headlines from Google News RSS.
2. Attempt yfinance news as a supplementary source.
3. Deduplicate headlines (normalised fingerprint).
4. Clean headlines (strip source suffixes, collapse whitespace).
5. Run FinBERT sentiment analysis.
6. Store results into ``news_sentiment`` table.
   - Duplicates are silently skipped via the unique constraint.

Usage
-----
::

    python -m scripts.collect_news          # from backend/
    python scripts/collect_news.py          # direct execution
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the backend directory is on sys.path when run directly.
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from scripts.config import SYMBOLS, setup_logging
from database import init_db, NewsSentiment
from database.database import get_db
from services.cleaning_service import clean_headline
from services.data_quality import deduplicate_headlines, normalize_to_ist
from services.finbert_service import analyze_sentiment
from services.news_service import fetch_news_headlines

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# yfinance news fallback
# ---------------------------------------------------------------------------

def _fetch_yfinance_news(symbol: str) -> list[dict]:
    """Attempt to fetch news from yfinance Ticker.news.

    Returns a list of ``{"headline": ..., "published_date": ...}`` dicts
    matching the shape expected by the rest of the pipeline.  Returns an
    empty list if the API is unavailable or returns nothing.
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        raw_news = getattr(ticker, "news", None)
        if not raw_news:
            return []

        articles = []
        for item in raw_news:
            title = item.get("title", "").strip()
            pub_ts = item.get("providerPublishTime")
            if not title or not pub_ts:
                continue

            pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
            articles.append({
                "headline": title,
                "published_date": pub_dt.isoformat(),
                "source": "yfinance",
            })

        logger.info("yfinance returned %d headline(s) for %s", len(articles), symbol)
        return articles

    except Exception as exc:
        logger.debug("yfinance news fallback failed for %s: %s", symbol, exc)
        return []


# ---------------------------------------------------------------------------
# Collection logic
# ---------------------------------------------------------------------------

def collect_for_symbol(symbol: str) -> dict:
    """Collect, score, and store headlines for a single symbol.

    Returns a dict of collection statistics.
    """
    stats = {
        "symbol": symbol,
        "google_news": 0,
        "yfinance_news": 0,
        "after_dedup": 0,
        "scored": 0,
        "inserted": 0,
        "skipped": 0,
        "errors": 0,
    }

    # --- 1. Fetch from Google News RSS ------------------------------------
    symbol_short = symbol.replace(".NS", "")
    try:
        google_articles = fetch_news_headlines(symbol_short)
        for a in google_articles:
            a.setdefault("source", "google_news_rss")
        stats["google_news"] = len(google_articles)
    except Exception as exc:
        logger.error("Google News RSS failed for %s: %s", symbol, exc)
        google_articles = []
        stats["errors"] += 1

    # --- 2. Fetch from yfinance (fallback) --------------------------------
    yf_articles = _fetch_yfinance_news(symbol)
    stats["yfinance_news"] = len(yf_articles)

    # --- 3. Merge and deduplicate -----------------------------------------
    all_articles = google_articles + yf_articles
    unique_articles = deduplicate_headlines(all_articles)
    stats["after_dedup"] = len(unique_articles)

    if not unique_articles:
        logger.info("No new headlines for %s", symbol)
        return stats

    # --- 4. Clean headlines -----------------------------------------------
    for article in unique_articles:
        article["cleaned_headline"] = clean_headline(article["headline"])

    # Remove articles with empty cleaned headlines
    cleaned_articles = [
        a for a in unique_articles if a.get("cleaned_headline")
    ]

    # --- 5. Run FinBERT sentiment -----------------------------------------
    # Prepare articles in the format expected by analyze_sentiment
    sentiment_input = [
        {"headline": a["cleaned_headline"], "published_date": a["published_date"]}
        for a in cleaned_articles
    ]

    try:
        scored = analyze_sentiment(sentiment_input)
        stats["scored"] = len(scored)
    except Exception as exc:
        logger.error("FinBERT scoring failed for %s: %s", symbol, exc)
        stats["errors"] += 1
        return stats

    # --- 6. Store into database -------------------------------------------
    with get_db() as db:
        for article, score in zip(cleaned_articles, scored):
            try:
                pub_date_str = article.get("published_date", "")
                try:
                    pub_dt = datetime.fromisoformat(pub_date_str).replace(
                        tzinfo=timezone.utc
                    )
                except (ValueError, TypeError):
                    pub_dt = datetime.now(timezone.utc)

                row = NewsSentiment(
                    symbol=symbol,
                    headline=article["headline"],
                    cleaned_headline=article.get("cleaned_headline"),
                    source=article.get("source", "google_news_rss"),
                    published_at=pub_dt,
                    sentiment_label=score.get("label"),
                    sentiment_confidence=score.get("confidence"),
                    sentiment_score=score.get("sentiment_score"),
                )
                db.add(row)
                db.commit()
                stats["inserted"] += 1

            except Exception:
                db.rollback()
                stats["skipped"] += 1

    return stats


def collect_all() -> list[dict]:
    """Run news collection for all configured symbols.

    Returns a list of per-symbol statistics dicts.
    """
    init_db()
    all_stats = []

    for symbol in SYMBOLS:
        logger.info("--- Collecting news for %s ---", symbol)
        s = collect_for_symbol(symbol)
        all_stats.append(s)
        logger.info(
            "%s: google=%d  yf=%d  dedup=%d  scored=%d  inserted=%d  skipped=%d  errors=%d",
            s["symbol"], s["google_news"], s["yfinance_news"],
            s["after_dedup"], s["scored"], s["inserted"],
            s["skipped"], s["errors"],
        )

    return all_stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging()
    logger.info("=== News Collection Started ===")
    results = collect_all()

    total_inserted = sum(r["inserted"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    logger.info(
        "=== News Collection Complete: %d inserted, %d errors across %d symbols ===",
        total_inserted, total_errors, len(results),
    )
