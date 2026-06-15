from datetime import datetime, timezone

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

Base = declarative_base()


def utcnow() -> datetime:
    """Timezone-aware UTC now (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


def make_engine(url: str = DATABASE_URL):
    """Build a SQLAlchemy engine, applying SQLite-friendly options when needed."""
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Enforce foreign keys on SQLite (off by default).
        @event.listens_for(engine, "connect")
        def _fk_pragma(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        return engine
    return create_engine(url, echo=False, pool_pre_ping=True)


engine = make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_all_tables(bind=None):
    """Create all database tables."""
    Base.metadata.create_all(bind=bind or engine)


def drop_all_tables(bind=None):
    """Drop all database tables (dev only)."""
    Base.metadata.drop_all(bind=bind or engine)
