"""FastAPI app serving the seeded teaching collections.

Each collection lives in its own Postgres schema (see ``potato-tornado seed``), so the API is
organised the same way: ``/collections`` lists the schemas, and each exposes its tables and rows.
Schema/table names in path params are always validated against the live catalog before being used
in a query, so the identifier interpolation in :func:`table_rows` cannot be injected.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from potato_tornado_service.db import get_engine
from potato_tornado_service.ui import INDEX_HTML

app = FastAPI(
    title="potato-tornado-service",
    description="Query the synthetic teaching collections seeded into Postgres.",
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    """Serve the dataset browser UI (a static page that drives the JSON API below)."""
    return INDEX_HTML

# Schemas that ship with Postgres / hold no collection data — hidden from the API.
_SYSTEM_SCHEMAS = frozenset({"pg_catalog", "information_schema", "pg_toast", "public"})


def _schemas(conn: Connection) -> list[str]:
    rows = conn.execute(
        text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
    )
    return [r[0] for r in rows if r[0] not in _SYSTEM_SCHEMAS]


def _tables(conn: Connection, schema: str) -> list[str]:
    rows = conn.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :schema ORDER BY table_name"
        ),
        {"schema": schema},
    )
    return [r[0] for r in rows]


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness + database connectivity check."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    return {"status": "ok"}


@app.get("/collections")
def collections() -> list[str]:
    """List the seeded collections (one Postgres schema each)."""
    with get_engine().connect() as conn:
        return _schemas(conn)


@app.get("/collections/{schema}/tables")
def collection_tables(schema: str) -> list[str]:
    """List the tables in one collection's schema."""
    with get_engine().connect() as conn:
        tables = _tables(conn, schema)
    if not tables:
        raise HTTPException(status_code=404, detail=f"no such collection: {schema!r}")
    return tables


@app.get("/collections/{schema}/tables/{table}")
def table_rows(
    schema: str,
    table: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Return a page of rows from one table as JSON records."""
    with get_engine().connect() as conn:
        if table not in _tables(conn, schema):
            raise HTTPException(status_code=404, detail=f"no such table: {schema}.{table}")
        # schema and table are validated against the catalog above, so quoting them here is safe.
        result = conn.execute(
            text(f'SELECT * FROM "{schema}"."{table}" LIMIT :limit OFFSET :offset'),
            {"limit": limit, "offset": offset},
        )
        columns = list(result.keys())
        rows = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
    return {"schema": schema, "table": table, "limit": limit, "offset": offset, "rows": rows}
