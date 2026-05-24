"""Daily automated data collection and research pipeline.

Orchestrates the full pipeline in sequence:

1. **Fetch news** — Google News RSS + yfinance fallback
2. **Analyze sentiment** — FinBERT scoring
3. **Store sentiment** — Insert into ``news_sentiment`` table
4. **Fetch stock prices** — OHLCV from yfinance
5. **Calculate indicators** — RSI, MACD
6. **Store prices** — Insert into ``stock_prices`` table
7. **Build research dataset** — Forward returns + abnormal returns

Each step is idempotent — the pipeline can be safely re-run without
creating duplicate data.  Failures in one step are logged but do not
prevent subsequent steps from executing.

Usage
-----
::

    python -m scripts.run_daily_pipeline    # from backend/
    python scripts/run_daily_pipeline.py    # direct execution

Schedule this script via cron (Linux) or Task Scheduler (Windows)
to run daily after market close.  See ``scheduler_examples.md``.
"""

import logging
import sys
import time
from pathlib import Path

_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from scripts.config import setup_logging

logger = logging.getLogger(__name__)


def run_pipeline() -> dict:
    """Execute the full daily pipeline.

    Returns a summary dict with timings and per-step results.
    """
    summary = {
        "news_collection": None,
        "stock_collection": None,
        "research_build": None,
        "total_time_seconds": 0,
        "success": True,
    }

    pipeline_start = time.time()

    # ----- Step 1: Collect news & sentiment -------------------------------
    logger.info("=" * 60)
    logger.info("STEP 1/3: News Collection & Sentiment Scoring")
    logger.info("=" * 60)
    try:
        from scripts.collect_news import collect_all as collect_news
        step_start = time.time()
        news_results = collect_news()
        step_time = time.time() - step_start
        summary["news_collection"] = {
            "results": news_results,
            "time_seconds": round(step_time, 1),
            "total_inserted": sum(r["inserted"] for r in news_results),
            "total_errors": sum(r["errors"] for r in news_results),
        }
        logger.info(
            "News collection complete in %.1fs: %d inserted, %d errors",
            step_time,
            summary["news_collection"]["total_inserted"],
            summary["news_collection"]["total_errors"],
        )
    except Exception as exc:
        logger.exception("News collection failed: %s", exc)
        summary["news_collection"] = {"error": str(exc)}
        summary["success"] = False

    # ----- Step 2: Collect stock prices -----------------------------------
    logger.info("=" * 60)
    logger.info("STEP 2/3: Stock Price Collection")
    logger.info("=" * 60)
    try:
        from scripts.collect_stock_data import collect_all as collect_stocks
        step_start = time.time()
        stock_results = collect_stocks()
        step_time = time.time() - step_start
        summary["stock_collection"] = {
            "results": stock_results,
            "time_seconds": round(step_time, 1),
            "total_inserted": sum(r["inserted"] for r in stock_results),
        }
        logger.info(
            "Stock collection complete in %.1fs: %d rows inserted",
            step_time,
            summary["stock_collection"]["total_inserted"],
        )
    except Exception as exc:
        logger.exception("Stock collection failed: %s", exc)
        summary["stock_collection"] = {"error": str(exc)}
        summary["success"] = False

    # ----- Step 3: Build research dataset ---------------------------------
    logger.info("=" * 60)
    logger.info("STEP 3/3: Research Dataset Build")
    logger.info("=" * 60)
    try:
        from scripts.build_research_dataset import build_all
        step_start = time.time()
        research_results = build_all()
        step_time = time.time() - step_start
        summary["research_build"] = {
            "results": research_results,
            "time_seconds": round(step_time, 1),
            "total_inserted": sum(r.get("inserted", 0) for r in research_results),
            "total_updated": sum(r.get("updated", 0) for r in research_results),
        }
        logger.info(
            "Research build complete in %.1fs: %d inserted, %d updated",
            step_time,
            summary["research_build"]["total_inserted"],
            summary["research_build"]["total_updated"],
        )
    except Exception as exc:
        logger.exception("Research build failed: %s", exc)
        summary["research_build"] = {"error": str(exc)}
        summary["success"] = False

    # ----- Summary --------------------------------------------------------
    summary["total_time_seconds"] = round(time.time() - pipeline_start, 1)

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info("Total time: %.1fs", summary["total_time_seconds"])
    logger.info("Success: %s", summary["success"])

    if summary["news_collection"] and "total_inserted" in summary["news_collection"]:
        logger.info(
            "  News:     %d headlines inserted",
            summary["news_collection"]["total_inserted"],
        )
    if summary["stock_collection"] and "total_inserted" in summary["stock_collection"]:
        logger.info(
            "  Prices:   %d rows inserted",
            summary["stock_collection"]["total_inserted"],
        )
    if summary["research_build"] and "total_inserted" in summary["research_build"]:
        logger.info(
            "  Research: %d metrics inserted, %d updated",
            summary["research_build"]["total_inserted"],
            summary["research_build"].get("total_updated", 0),
        )

    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging()
    logger.info("=== Daily Pipeline Started ===")
    result = run_pipeline()

    exit_code = 0 if result["success"] else 1
    sys.exit(exit_code)
