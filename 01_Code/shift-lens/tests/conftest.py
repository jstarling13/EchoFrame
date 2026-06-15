"""Shared pytest fixtures: an isolated SQLite-backed DB session per test."""

import pytest
from sqlalchemy.orm import sessionmaker

from models.base import Base, make_engine
# Import models so they register on Base.metadata before create_all.
import models  # noqa: F401


@pytest.fixture
def db_session(tmp_path):
    """A fresh SQLite database (file-backed, isolated per test)."""
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = make_engine(url)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
