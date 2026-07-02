"""Database engine, lazily built from settings and cached for the process."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from potato_tornado_service.config import load_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a process-wide SQLAlchemy engine (``pool_pre_ping`` guards stale connections)."""
    return create_engine(load_settings().database_url, pool_pre_ping=True)
