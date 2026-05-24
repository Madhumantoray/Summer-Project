"""Data quality utilities for the stock research pipeline.

This module centralises all data-cleaning, timezone-handling, and
market-calendar logic so that collection scripts and research services
produce consistent, bias-free datasets.

Key design decisions
--------------------
- **IST (Asia/Kolkata)** is the canonical timezone for NSE equities.
- News published after 15:30 IST is attributed to the *next* trading
  day to avoid look-ahead bias (the market has already closed).
- Weekends and known NSE holidays are skipped when computing forward
  trading-day offsets.
"""

import hashlib
import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timezone constants
# ---------------------------------------------------------------------------

IST = timezone(timedelta(hours=5, minutes=30))
NSE_MARKET_CLOSE = time(15, 30)  # 15:30 IST

# Known NSE holidays (2024-2026).  Extend as needed.
_NSE_HOLIDAYS = {
    # 2024
    date(2024, 1, 26), date(2024, 3, 8), date(2024, 3, 25),
    date(2024, 3, 29), date(2024, 4, 11), date(2024, 4, 14),
    date(2024, 4, 17), date(2024, 4, 21), date(2024, 5, 1),
    date(2024, 5, 23), date(2024, 6, 17), date(2024, 7, 17),
    date(2024, 8, 15), date(2024, 10, 2), date(2024, 10, 12),
    date(2024, 10, 31), date(2024, 11, 1), date(2024, 11, 15),
    date(2024, 12, 25),
    # 2025
    date(2025, 2, 26), date(2025, 3, 14), date(2025, 3, 31),
    date(2025, 4, 10), date(2025, 4, 14), date(2025, 4, 18),
    date(2025, 5, 1), date(2025, 5, 12), date(2025, 6, 27),
    date(2025, 8, 15), date(2025, 8, 27), date(2025, 10, 2),
    date(2025, 10, 21), date(2025, 10, 22), date(2025, 11, 5),
    date(2025, 11, 26), date(2025, 12, 25),
    # 2026
    date(2026, 1, 26), date(2026, 3, 3), date(2026, 3, 19),
    date(2026, 3, 20), date(2026, 4, 3), date(2026, 4, 14),
    date(2026, 5, 1), date(2026, 5, 25), date(2026, 7, 7),
    date(2026, 8, 15), date(2026, 10, 2), date(2026, 10, 20),
    date(2026, 10, 21), date(2026, 11, 9), date(2026, 11, 25),
    date(2026, 12, 25),
}


# ---------------------------------------------------------------------------
# Trading calendar
# ---------------------------------------------------------------------------

def is_trading_day(d: date) -> bool:
    """Return True if *d* is a regular NSE trading day.

    A day is *not* a trading day if it falls on a weekend (Saturday
    or Sunday) or is in the known NSE holiday set.
    """
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return d not in _NSE_HOLIDAYS


def get_next_trading_day(d: date) -> date:
    """Return the next NSE trading day on or after *d*.

    If *d* itself is a trading day, return *d* unchanged.
    """
    current = d
    # Safety limit to avoid infinite loop if calendar data is missing
    for _ in range(30):
        if is_trading_day(current):
            return current
        current += timedelta(days=1)
    # Fallback: return the input + 1 if we couldn't find a trading day
    logger.warning("Could not find trading day within 30 days of %s", d)
    return d + timedelta(days=1)


def get_trading_day_offset(d: date, offset: int) -> date:
    """Return the trading day *offset* trading days after *d*.

    Parameters
    ----------
    d : date
        The starting date (should itself be a trading day).
    offset : int
        Number of trading days to advance.  Must be >= 0.

    Returns
    -------
    date
        The target trading day, or *d* if offset is 0.
    """
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if offset == 0:
        return get_next_trading_day(d)

    current = d
    days_counted = 0
    for _ in range(offset * 4):  # generous upper bound
        current += timedelta(days=1)
        if is_trading_day(current):
            days_counted += 1
        if days_counted >= offset:
            return current

    logger.warning(
        "Could not advance %d trading days from %s; returning best effort", offset, d
    )
    return current


# ---------------------------------------------------------------------------
# Timezone handling
# ---------------------------------------------------------------------------

def normalize_to_ist(dt: datetime) -> datetime:
    """Convert a datetime to IST (Asia/Kolkata, UTC+05:30).

    If the input is timezone-naive, it is assumed to be UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def align_to_market_hours(published_at: datetime) -> date:
    """Map a publication timestamp to its effective trading date.

    Rules
    -----
    - If published *before* 15:30 IST on a trading day → that day.
    - If published *after* 15:30 IST → next trading day.
    - If published on a weekend or holiday → next trading day.

    This prevents look-ahead bias: news arriving after market close
    cannot influence the same day's closing price.
    """
    ist_dt = normalize_to_ist(published_at)
    pub_date = ist_dt.date()
    pub_time = ist_dt.time()

    if not is_trading_day(pub_date) or pub_time >= NSE_MARKET_CLOSE:
        return get_next_trading_day(pub_date + timedelta(days=1))

    return pub_date


# ---------------------------------------------------------------------------
# Headline deduplication
# ---------------------------------------------------------------------------

def _headline_fingerprint(headline: str) -> str:
    """Create a normalised fingerprint for near-duplicate detection."""
    normalised = headline.lower().strip()
    # Remove common filler words that differ across sources
    for word in ("- ", "| ", ": "):
        normalised = normalised.replace(word, " ")
    normalised = " ".join(normalised.split())
    return hashlib.md5(normalised.encode("utf-8")).hexdigest()


def deduplicate_headlines(articles: List[dict]) -> List[dict]:
    """Remove exact and near-duplicate headlines from a list of articles.

    Uses a normalised MD5 fingerprint so that minor punctuation or
    whitespace differences don't cause duplicates.
    """
    seen = set()
    unique_articles = []
    for article in articles:
        fp = _headline_fingerprint(article.get("headline", ""))
        if fp not in seen:
            seen.add(fp)
            unique_articles.append(article)

    removed = len(articles) - len(unique_articles)
    if removed > 0:
        logger.info("Deduplicated %d headline(s) from batch of %d", removed, len(articles))

    return unique_articles


# ---------------------------------------------------------------------------
# Missing value handling
# ---------------------------------------------------------------------------

def handle_missing_prices(df: pd.DataFrame, strategy: str = "forward_fill") -> pd.DataFrame:
    """Fill gaps in price data using the specified strategy.

    Parameters
    ----------
    df : DataFrame
        Must contain at least a ``close`` column.
    strategy : str
        One of ``"forward_fill"``, ``"drop"``, or ``"interpolate"``.

    Returns
    -------
    DataFrame
        Cleaned dataframe.
    """
    if df.empty:
        return df

    price_cols = ["open", "high", "low", "close"]
    existing_cols = [c for c in price_cols if c in df.columns]

    if strategy == "forward_fill":
        df[existing_cols] = df[existing_cols].ffill()
    elif strategy == "drop":
        df = df.dropna(subset=existing_cols)
    elif strategy == "interpolate":
        df[existing_cols] = df[existing_cols].interpolate(method="linear")
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return df
