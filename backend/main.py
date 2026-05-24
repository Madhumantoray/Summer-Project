import logging
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

logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Research API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=get_rate_limit())


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
