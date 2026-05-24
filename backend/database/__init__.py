"""Database package for the stock research platform.

Provides SQLAlchemy models, engine configuration, and session management
for persistent storage of news sentiment, stock prices, and research metrics.
"""

from database.database import SessionLocal, engine, get_db, init_db
from database.models import Base, NewsSentiment, ResearchMetric, StockPrice

__all__ = [
    "Base",
    "NewsSentiment",
    "StockPrice",
    "ResearchMetric",
    "SessionLocal",
    "engine",
    "get_db",
    "init_db",
]
