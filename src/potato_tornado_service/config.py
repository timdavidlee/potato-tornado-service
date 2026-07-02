"""Service configuration, read from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5432/teaching"


def _normalize_dsn(dsn: str) -> str:
    """Route a bare ``postgresql://`` / ``postgres://`` DSN to the psycopg 3 driver.

    SQLAlchemy maps the bare scheme to psycopg2, which isn't installed; the app (like
    ``potato_tornado``'s ``PostgresSink``) uses psycopg 3, addressed as ``postgresql+psycopg://``.
    """
    for prefix in ("postgresql://", "postgres://"):
        if dsn.startswith(prefix):
            return "postgresql+psycopg://" + dsn[len(prefix) :]
    return dsn


@dataclass(frozen=True, slots=True)
class Settings:
    """Resolved service settings."""

    database_url: str


def load_settings() -> Settings:
    """Build :class:`Settings` from ``DATABASE_URL`` (falling back to a local default)."""
    return Settings(database_url=_normalize_dsn(os.environ.get("DATABASE_URL", _DEFAULT_DSN)))
