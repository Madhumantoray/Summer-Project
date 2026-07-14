import re
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD

TIMEFRAME_MAP = {
    "1D": "1d",
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "5Y": "5y",
}

INDICATOR_COLUMNS = ["RSI", "MACD", "MACD_SIGNAL", "MACD_DIFF"]
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,20}$")


def get_stock_records(
    symbol: str,
    timeframe: str = "1Y",
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    validate_inputs(symbol=symbol, timeframe=timeframe, start=start, end=end)
    ticker = normalize_nse_symbol(symbol)
    df = download_price_history(ticker=ticker, timeframe=timeframe, start=start, end=end)

    if df.empty:
        return {"error": "No stock data found"}

    df = prepare_price_frame(df)
    df = add_indicators(df)
    df["Date"] = df["Date"].astype(str)

    return df.to_dict(orient="records")


def normalize_nse_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol.endswith(".NS"):
        symbol += ".NS"
    return symbol


def validate_inputs(
    symbol: str,
    timeframe: str,
    start: Optional[str],
    end: Optional[str],
) -> None:
    normalized_symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized_symbol):
        raise ValueError("Invalid symbol")

    if timeframe not in TIMEFRAME_MAP:
        raise ValueError("Invalid timeframe")

    if start:
        parse_date(start)

    if end:
        parse_date(end)

    if start and end and parse_date(start) > parse_date(end):
        raise ValueError("Start date must be before end date")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid date format. Use YYYY-MM-DD") from exc


def download_price_history(
    ticker: str,
    timeframe: str,
    start: Optional[str],
    end: Optional[str],
) -> pd.DataFrame:
    if start and end:
        return yf.download(
            ticker,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,
            progress=False,
        )

    return yf.download(
        ticker,
        period=TIMEFRAME_MAP.get(timeframe, "1y"),
        interval="1d",
        auto_adjust=True,
        progress=False,
    )


def prepare_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    price_frame = df.copy()
    price_frame.reset_index(inplace=True)
    price_frame.columns = [
        column[0] if isinstance(column, tuple) else column
        for column in price_frame.columns
    ]
    price_frame.rename(columns={price_frame.columns[0]: "Date"}, inplace=True)
    return price_frame


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    indicator_frame = df.copy()

    rsi = RSIIndicator(close=indicator_frame["Close"])
    indicator_frame["RSI"] = rsi.rsi()

    macd = MACD(close=indicator_frame["Close"])
    indicator_frame["MACD"] = macd.macd()
    indicator_frame["MACD_SIGNAL"] = macd.macd_signal()
    indicator_frame["MACD_DIFF"] = macd.macd_diff()

    for column in INDICATOR_COLUMNS:
        indicator_frame[column] = indicator_frame[column].fillna(0)

    return indicator_frame
