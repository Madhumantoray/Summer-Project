"""Research service for computing forward returns and abnormal returns.

This is the CORE research computation module.  It takes a sentiment
observation date for a given stock and computes how the stock performed
over the subsequent 1, 3, 7, and 30 trading days.

Formulas
--------
Daily return::

    r_t = (P_t - P_{t-1}) / P_{t-1}

Future N-day return::

    future_return_N = (P_{t+N} - P_t) / P_t

Abnormal return (market-adjusted)::

    abnormal_return = stock_return - benchmark_return

Look-ahead bias prevention
--------------------------
- Future returns are computed using prices *after* the sentiment date.
- After-market news (published after 15:30 IST) is shifted to the
  next trading day via ``data_quality.align_to_market_hours``.
- Only completed return windows are stored.  If the t+N price doesn't
  exist yet (e.g. for recent sentiment), the field is left NULL.
"""

import logging
from datetime import date
from typing import Optional

import pandas as pd

from services.data_quality import get_next_trading_day, get_trading_day_offset

logger = logging.getLogger(__name__)

RETURN_WINDOWS = [1, 3, 7, 30]


# ---------------------------------------------------------------------------
# Forward return computation
# ---------------------------------------------------------------------------

def compute_future_returns(
    observation_date: date,
    prices_df: pd.DataFrame,
) -> dict[str, Optional[float]]:
    """Compute future returns over standard windows from a single date.

    Parameters
    ----------
    observation_date : date
        The date of the sentiment observation (already market-aligned).
    prices_df : DataFrame
        Must have columns ``date`` (Python date) and ``close`` (float),
        sorted by date ascending.

    Returns
    -------
    dict
        Keys: ``future_return_1d``, ``future_return_3d``, etc.
        Values: float or None if the window extends beyond available data.
    """
    results = {}
    price_lookup = dict(zip(prices_df["date"], prices_df["close"]))

    # t=0: the observation date itself (or next trading day if not available)
    t0_date = get_next_trading_day(observation_date)
    p_t0 = price_lookup.get(t0_date)

    if p_t0 is None or p_t0 == 0:
        # No price on the observation date — can't compute returns.
        for n in RETURN_WINDOWS:
            results[f"future_return_{n}d"] = None
        return results

    for n in RETURN_WINDOWS:
        t_n_date = get_trading_day_offset(t0_date, n)
        p_tn = price_lookup.get(t_n_date)

        if p_tn is not None and p_t0 != 0:
            results[f"future_return_{n}d"] = round((p_tn - p_t0) / p_t0, 6)
        else:
            results[f"future_return_{n}d"] = None

    return results


def compute_abnormal_returns(
    stock_returns: dict[str, Optional[float]],
    benchmark_returns: dict[str, Optional[float]],
) -> dict[str, Optional[float]]:
    """Compute abnormal returns for 1-day and 7-day windows.

    Abnormal return = stock return − benchmark (market) return.

    Parameters
    ----------
    stock_returns : dict
        Output of ``compute_future_returns`` for the stock.
    benchmark_returns : dict
        Output of ``compute_future_returns`` for the benchmark index.

    Returns
    -------
    dict
        ``{"abnormal_return_1d": ..., "abnormal_return_7d": ...}``
    """
    results = {}

    for n in [1, 7]:
        stock_r = stock_returns.get(f"future_return_{n}d")
        bench_r = benchmark_returns.get(f"future_return_{n}d")

        if stock_r is not None and bench_r is not None:
            results[f"abnormal_return_{n}d"] = round(stock_r - bench_r, 6)
        else:
            results[f"abnormal_return_{n}d"] = None

    return results


# ---------------------------------------------------------------------------
# Batch computation
# ---------------------------------------------------------------------------

def build_research_metrics(
    symbol: str,
    sentiment_dates: list[tuple[date, float]],
    stock_prices_df: pd.DataFrame,
    benchmark_prices_df: pd.DataFrame,
) -> list[dict]:
    """Compute research metrics for a list of sentiment observation dates.

    Parameters
    ----------
    symbol : str
        The stock symbol (e.g. ``"RELIANCE.NS"``).
    sentiment_dates : list of (date, sentiment_score) tuples
        Dates when sentiment was observed, already market-aligned.
    stock_prices_df : DataFrame
        Daily prices for the stock (columns: ``date``, ``close``).
    benchmark_prices_df : DataFrame
        Daily prices for the benchmark (columns: ``date``, ``close``).

    Returns
    -------
    list of dict
        One dict per sentiment date with all computed metrics.
    """
    metrics = []

    for obs_date, sentiment_score in sentiment_dates:
        stock_returns = compute_future_returns(obs_date, stock_prices_df)
        bench_returns = compute_future_returns(obs_date, benchmark_prices_df)
        abnormal = compute_abnormal_returns(stock_returns, bench_returns)

        row = {
            "symbol": symbol,
            "date": obs_date,
            "sentiment_score": sentiment_score,
            **stock_returns,
            **abnormal,
        }
        metrics.append(row)

    logger.info(
        "Computed %d research metrics for %s", len(metrics), symbol,
    )
    return metrics
