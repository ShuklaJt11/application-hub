from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.main as main_module


@pytest.mark.asyncio
async def test_lifespan_disposes_engine(monkeypatch):
    dispose_mock = AsyncMock()
    fake_engine = SimpleNamespace(dispose=dispose_mock)

    monkeypatch.setattr(main_module, "engine", fake_engine)

    async with main_module.lifespan(None):
        pass

    dispose_mock.assert_awaited_once()
