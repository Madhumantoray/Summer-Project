"""Shared configuration for data collection and research scripts.

All collection scripts import symbols, benchmark, and logging setup
from here so changes propagate to the entire pipeline.
"""

import logging
import sys

# ---------------------------------------------------------------------------
# Stock universe
# ---------------------------------------------------------------------------

SYMBOLS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
]

# Nifty 50 index — used as the market benchmark for abnormal returns.
BENCHMARK = "^NSEI"

# yfinance period string for historical stock price downloads.
HISTORY_PERIOD = "5y"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger for pipeline scripts.

    Call this at the top of every standalone script so that log output
    is consistent across collection, research, and pipeline runs.
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout,
    )
