"""Health-endpoint tests that don't require a live database."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from potato_tornado_service import db, main


def test_health_ok_when_db_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Conn:
        def __enter__(self) -> _Conn:
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def execute(self, *_: object) -> None:
            pass

    monkeypatch.setattr(db, "get_engine", lambda: type("E", (), {"connect": lambda self: _Conn()})())
    monkeypatch.setattr(main, "get_engine", db.get_engine)
    response = TestClient(main.app).get("/health")
    assert response.json() == {"status": "ok"}


def test_index_serves_ui() -> None:
    response = TestClient(main.app).get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "dataset browser" in response.text


def test_health_503_when_db_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> object:
        class _E:
            def connect(self) -> object:
                raise OperationalError("SELECT 1", {}, Exception("refused"))

        return _E()

    monkeypatch.setattr(main, "get_engine", _boom)
    response = TestClient(main.app, raise_server_exceptions=False).get("/health")
    assert response.status_code == 503
