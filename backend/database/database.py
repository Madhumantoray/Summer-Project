"""SQLAlchemy engine, session factory, and database initialisation.

The database file lives at ``backend/database/stocks.db`` by default.
Override with the ``STOCK_DB_URL`` environment variable if needed
(e.g. to point at PostgreSQL for production).

Usage
-----
::

    from database.database import get_db, init_db

    # Create tables on startup
    init_db()

    # Inside a request or script
    with get_db() as session:
        session.add(row)
        session.commit()
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.models import Base

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_DB_DIR = Path(__file__).resolve().parent
_DEFAULT_DB_PATH = _DB_DIR / "stocks.db"
_DEFAULT_DB_URL = f"sqlite:///{_DEFAULT_DB_PATH}"

DATABASE_URL = os.getenv("STOCK_DB_URL", _DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    # SQLite needs check_same_thread=False when used with FastAPI
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)


# Enable WAL mode and foreign keys for SQLite connections.
@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Optimise SQLite for concurrent reads during research queries."""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_db():
    """Yield a database session and guarantee cleanup.

    Usage::

        with get_db() as db:
            db.query(StockPrice).filter_by(symbol="RELIANCE.NS").all()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db():
    """Create all tables that don't already exist.

    Safe to call multiple times — SQLAlchemy's ``create_all`` is a no-op
    for tables that are already present.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified at %s", DATABASE_URL)
