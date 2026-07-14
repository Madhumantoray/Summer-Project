import logging
import re
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.security import (
        RateLimitMiddleware,
        SecurityHeadersMiddleware,
        get_allowed_origins,
        get_rate_limit,
    )
except ModuleNotFoundError:
    from security import (
        RateLimitMiddleware,
        SecurityHeadersMiddleware,
        get_allowed_origins,
        get_rate_limit,
    )

try:
    from backend.services.stock_data import get_stock_records
    from backend.services.sentiment_service import get_sentiment_records
except ModuleNotFoundError:
    from services.stock_data import get_stock_records
    from services.sentiment_service import get_sentiment_records

try:
    from backend.database import init_db, ResearchMetric
    from backend.database.database import get_db
except ModuleNotFoundError:
    from database import init_db, ResearchMetric
    from database.database import get_db

logger = logging.getLogger(__name__)

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,20}$")


# ---------------------------------------------------------------------------
# Lifespan — initialise database tables on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create database tables on startup (no-op if they already exist)."""
    init_db()
    logger.info("Database initialised on startup")
    yield


app = FastAPI(title="Stock Research API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=get_rate_limit())


# ---------------------------------------------------------------------------
# Existing endpoints (unchanged)
# ---------------------------------------------------------------------------


@app.get("/")
def home():
    return {"message": "Stock API Running"}


@app.get("/stock/{symbol}")
def get_stock(
    symbol: str,
    timeframe: str = Query(default="1Y"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
):
    try:
        return get_stock_records(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception:
        return {"error": "Unexpected server error"}


@app.get("/sentiment/{symbol}")
def get_sentiment(symbol: str):
    try:
        return get_sentiment_records(symbol=symbol)
    except ValueError as exc:
        return {"error": str(exc)}
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "required package"
        return {"error": f"Missing backend dependency: {missing_package}"}
    except ImportError as exc:
        return {"error": f"Unable to import sentiment dependency: {exc}"}
    except RuntimeError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        logger.exception("Sentiment analysis failed for symbol %s", symbol)
        return {"error": "Unable to analyze sentiment"}

@app.get("/news/{symbol}")
def get_news(symbol: str):
    """Return raw news headlines with FinBERT sentiment from the database."""
    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        return {"error": "Invalid symbol"}

    db_symbol = f"{normalized}.NS" if not normalized.endswith(".NS") else normalized

    try:
        try:
            from backend.database.models import NewsSentiment
        except ModuleNotFoundError:
            from database.models import NewsSentiment

        with get_db() as db:
            rows = (
                db.query(NewsSentiment)
                .filter(NewsSentiment.symbol == db_symbol)
                .order_by(NewsSentiment.published_at.desc())
                .limit(75)
                .all()
            )

        return [
            {
                "symbol": r.symbol,
                "headline": r.headline,
                "source": r.source,
                "published_at": r.published_at.isoformat() if r.published_at else None,
                "sentiment_label": r.sentiment_label,
                "sentiment_confidence": r.sentiment_confidence,
                "sentiment_score": r.sentiment_score,
            }
            for r in rows
        ]
    except Exception:
        logger.exception("News query failed for %s", symbol)
        return {"error": "Unable to fetch news"}


# ---------------------------------------------------------------------------
# Research endpoints (new)
# ---------------------------------------------------------------------------


@app.get("/research/metrics/{symbol}")
def get_research_metrics(symbol: str):
    """Return computed research metrics (forward returns, abnormal returns)
    from the database for a given symbol."""
    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        return {"error": "Invalid symbol"}

    # Append .NS for NSE symbols if not already present
    db_symbol = f"{normalized}.NS" if not normalized.endswith(".NS") else normalized

    try:
        with get_db() as db:
            rows = (
                db.query(ResearchMetric)
                .filter(ResearchMetric.symbol == db_symbol)
                .order_by(ResearchMetric.date)
                .all()
            )

            if not rows:
                return {"error": f"No research metrics found for {db_symbol}"}

            return [
                {
                    "date": str(r.date),
                    "sentiment_score": r.sentiment_score,
                    "future_return_1d": r.future_return_1d,
                    "future_return_3d": r.future_return_3d,
                    "future_return_7d": r.future_return_7d,
                    "future_return_30d": r.future_return_30d,
                    "abnormal_return_1d": r.abnormal_return_1d,
                    "abnormal_return_7d": r.abnormal_return_7d,
                }
                for r in rows
            ]
    except Exception as exc:
        logger.exception("Research metrics query failed for %s", symbol)
        return {"error": "Unable to fetch research metrics"}


@app.get("/research/correlation")
def get_correlation_summary():
    """Return a quick correlation summary between sentiment and returns."""
    try:
        import numpy as np
        from scipy import stats as scipy_stats

        with get_db() as db:
            rows = db.query(ResearchMetric).all()

        if not rows:
            return {"error": "No research metrics available — run the pipeline first"}

        sentiments = []
        returns_7d = []
        for r in rows:
            if r.sentiment_score is not None and r.future_return_7d is not None:
                sentiments.append(r.sentiment_score)
                returns_7d.append(r.future_return_7d)

        if len(sentiments) < 3:
            return {"error": "Insufficient data for correlation analysis"}

        pearson_r, pearson_p = scipy_stats.pearsonr(sentiments, returns_7d)
        spearman_r, spearman_p = scipy_stats.spearmanr(sentiments, returns_7d)

        return {
            "n": len(sentiments),
            "pearson": {"r": round(pearson_r, 4), "p_value": round(pearson_p, 4)},
            "spearman": {"rho": round(spearman_r, 4), "p_value": round(spearman_p, 4)},
            "sentiment_mean": round(float(np.mean(sentiments)), 4),
            "return_7d_mean": round(float(np.mean(returns_7d)), 4),
        }
    except ImportError:
        return {"error": "scipy is required for correlation analysis"}
    except Exception as exc:
        logger.exception("Correlation analysis failed")
        return {"error": "Unable to compute correlations"}


@app.get("/research/pipeline/status")
def get_pipeline_status():
    """Return counts of records in each research table."""
    try:
        try:
            from backend.database.models import NewsSentiment, StockPrice
        except ModuleNotFoundError:
            from database.models import NewsSentiment, StockPrice

        with get_db() as db:
            news_count = db.query(NewsSentiment).count()
            price_count = db.query(StockPrice).count()
            metric_count = db.query(ResearchMetric).count()

            # Get unique symbols
            news_symbols = (
                db.query(NewsSentiment.symbol)
                .distinct()
                .all()
            )
            price_symbols = (
                db.query(StockPrice.symbol)
                .distinct()
                .all()
            )

        return {
            "news_sentiment": {
                "total_records": news_count,
                "symbols": [s[0] for s in news_symbols],
            },
            "stock_prices": {
                "total_records": price_count,
                "symbols": [s[0] for s in price_symbols],
            },
            "research_metrics": {
                "total_records": metric_count,
            },
        }
    except Exception as exc:
        logger.exception("Pipeline status query failed")
        return {"error": "Unable to query pipeline status"}
