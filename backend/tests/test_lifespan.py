from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import app.main as main_module


@pytest.mark.asyncio
async def test_lifespan_disposes_engine(monkeypatch):
    dispose_mock = AsyncMock()
    fake_engine = SimpleNamespace(dispose=dispose_mock)
    fake_redis_client = AsyncMock()
    fake_scheduler = SimpleNamespace(
        add_job=Mock(),
        start=Mock(),
        shutdown=Mock(),
    )

    monkeypatch.setattr(main_module, "engine", fake_engine)
    monkeypatch.setattr(
        main_module.redis, "from_url", lambda *args, **kwargs: fake_redis_client
    )
    monkeypatch.setattr(main_module.FastAPILimiter, "init", AsyncMock())
    monkeypatch.setattr(main_module.FastAPILimiter, "close", AsyncMock())
    monkeypatch.setattr(main_module, "AsyncIOScheduler", lambda: fake_scheduler)

    async with main_module.lifespan(None):
        pass

    assert fake_scheduler.add_job.call_count == 2
    fake_scheduler.start.assert_called_once()
    fake_scheduler.shutdown.assert_called_once_with(wait=False)
    dispose_mock.assert_awaited_once()
