from unittest.mock import Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.session as session_module
from app.db.session import get_db


@pytest.mark.asyncio
async def test_get_db_yields_async_session():
    agen = get_db()
    db = await anext(agen)
    assert isinstance(db, AsyncSession)
    await agen.aclose()


class _FakeConn:
    def __init__(self):
        self.info: dict[str, float] = {}


def test_before_cursor_execute_sets_start_time(monkeypatch):
    conn = _FakeConn()
    monkeypatch.setattr(session_module.time, "perf_counter", lambda: 123.45)

    session_module.before_cursor_execute(conn, None, "SELECT 1", None, None, False)

    assert conn.info["query_start_time"] == 123.45


def test_after_cursor_execute_skips_when_start_time_missing(monkeypatch):
    conn = _FakeConn()
    warning_mock = Mock()
    monkeypatch.setattr(session_module.logger, "warning", warning_mock)

    session_module.after_cursor_execute(conn, None, "SELECT 1", None, None, False)

    warning_mock.assert_not_called()


def test_after_cursor_execute_logs_slow_query(monkeypatch):
    conn = _FakeConn()
    conn.info["query_start_time"] = 10.0
    monkeypatch.setattr(
        session_module.time,
        "perf_counter",
        lambda: 10.0 + session_module.SLOW_QUERY_THRESHOLD + 0.05,
    )
    warning_mock = Mock()
    monkeypatch.setattr(session_module.logger, "warning", warning_mock)

    session_module.after_cursor_execute(conn, None, "SELECT 1", None, None, False)

    warning_mock.assert_called_once()
    args, kwargs = warning_mock.call_args
    assert args[0] == "Slow query detected"
    assert kwargs["extra"]["query"] == "SELECT 1"
    assert kwargs["extra"]["duration_ms"] > kwargs["extra"]["threshold_ms"]
    assert "query_start_time" not in conn.info
