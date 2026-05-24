"""SQLAlchemy ORM models for the stock research database.

Tables
------
news_sentiment
    Stores individual news headlines with FinBERT sentiment scores.
    Deduplicated on (symbol, headline, published_at).

stock_prices
    Stores daily OHLCV data with computed technical indicators.
    Deduplicated on (symbol, date).

research_metrics
    Stores computed forward returns and abnormal returns aligned
    to sentiment observation dates.  This is the core table for
    correlation analysis and event studies.
    Deduplicated on (symbol, date).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class NewsSentiment(Base):
    """A single news headline with its FinBERT sentiment score.

    The unique constraint on (symbol, headline, published_at) prevents
    the same headline from being stored more than once per symbol,
    which is critical for idempotent daily collection runs.
    """

    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    headline = Column(String, nullable=False)
    cleaned_headline = Column(String, nullable=True)
    source = Column(String, nullable=False, default="google_news_rss")
    published_at = Column(DateTime(timezone=True), nullable=False)
    sentiment_label = Column(String, nullable=True)          # positive / negative / neutral
    sentiment_confidence = Column(Float, nullable=True)      # 0.0 – 1.0
    sentiment_score = Column(Float, nullable=True)           # +conf / 0 / -conf
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "symbol", "headline", "published_at",
            name="uq_news_sentiment_symbol_headline_published",
        ),
    )

    def __repr__(self):
        return (
            f"<NewsSentiment(symbol={self.symbol!r}, "
            f"label={self.sentiment_label!r}, "
            f"score={self.sentiment_score}, "
            f"published_at={self.published_at})>"
        )


class StockPrice(Base):
    """Daily OHLCV data with computed technical indicators.

    One row per symbol per trading day.  Indicators (RSI, MACD) are
    computed during collection and stored alongside price data so that
    research queries don't need to recompute them.
    """

    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "symbol", "date",
            name="uq_stock_prices_symbol_date",
        ),
    )

    def __repr__(self):
        return (
            f"<StockPrice(symbol={self.symbol!r}, "
            f"date={self.date}, close={self.close})>"
        )


class ResearchMetric(Base):
    """Forward returns and abnormal returns for a sentiment observation date.

    Each row ties a daily sentiment score to the stock's subsequent
    performance over 1-, 3-, 7-, and 30-day windows.  Abnormal returns
    are computed relative to the Nifty 50 (^NSEI) benchmark.

    Look-ahead bias prevention
    --------------------------
    - ``future_return_Nd`` uses the closing price N trading days *after*
      the sentiment date, never before.
    - After-market news (published after 15:30 IST) is shifted to the
      next trading day before return computation.
    """

    __tablename__ = "research_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    sentiment_score = Column(Float, nullable=True)
    future_return_1d = Column(Float, nullable=True)
    future_return_3d = Column(Float, nullable=True)
    future_return_7d = Column(Float, nullable=True)
    future_return_30d = Column(Float, nullable=True)
    abnormal_return_1d = Column(Float, nullable=True)
    abnormal_return_7d = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "symbol", "date",
            name="uq_research_metrics_symbol_date",
        ),
    )

    def __repr__(self):
        return (
            f"<ResearchMetric(symbol={self.symbol!r}, "
            f"date={self.date}, "
            f"sentiment={self.sentiment_score}, "
            f"ret_7d={self.future_return_7d})>"
        )
