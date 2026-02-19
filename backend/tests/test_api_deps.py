import importlib
from unittest.mock import AsyncMock, Mock

import pytest

from app.api import deps


@pytest.mark.asyncio
async def test_get_redis_yields_client_and_closes(monkeypatch):
    fake_client = AsyncMock()
    from_url_mock = Mock(return_value=fake_client)

    monkeypatch.setattr(deps.redis, "from_url", from_url_mock)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/1")

    generator = deps.get_redis()
    yielded = await generator.__anext__()

    assert yielded is fake_client
    from_url_mock.assert_called_once_with(
        "redis://localhost:6390/1",
        encoding="utf-8",
        decode_responses=True,
    )

    await generator.aclose()
    fake_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_redis_uses_default_url(monkeypatch):
    fake_client = AsyncMock()
    from_url_mock = Mock(return_value=fake_client)

    monkeypatch.setattr(deps.redis, "from_url", from_url_mock)
    monkeypatch.delenv("REDIS_URL", raising=False)

    generator = deps.get_redis()
    await generator.__anext__()
    await generator.aclose()

    from_url_mock.assert_called_once_with(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True,
    )


@pytest.mark.asyncio
async def test_get_auth_service_returns_auth_service(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_SECRET", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_EXPIRE_MINUTES", "1440")

    auth_module = importlib.import_module("app.services.auth_services")
    auth_module = importlib.reload(auth_module)

    fake_db = object()
    fake_redis = object()

    service = await deps.get_auth_service(db=fake_db, redis_client=fake_redis)

    assert isinstance(service, auth_module.AuthService)
    assert service.db is fake_db
    assert service.redis_client is fake_redis
