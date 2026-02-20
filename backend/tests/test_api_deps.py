import importlib
import sys
import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture
def deps_module(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_SECRET", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_EXPIRE_MINUTES", "1440")

    sys.modules.pop("app.core.security", None)
    sys.modules.pop("app.api.deps", None)
    return importlib.import_module("app.api.deps")


@pytest.mark.asyncio
async def test_get_redis_yields_client_and_closes(monkeypatch, deps_module):
    fake_client = AsyncMock()
    from_url_mock = Mock(return_value=fake_client)

    monkeypatch.setattr(deps_module.redis, "from_url", from_url_mock)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/1")

    generator = deps_module.get_redis()
    yielded = await generator.__anext__()

    assert yielded is fake_client
    from_url_mock.assert_called_once_with(
        "redis://localhost:6390/1",
        encoding="utf-8",
        decode_responses=True,
    )

    await generator.aclose()
    fake_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_redis_uses_default_url(monkeypatch, deps_module):
    fake_client = AsyncMock()
    from_url_mock = Mock(return_value=fake_client)

    monkeypatch.setattr(deps_module.redis, "from_url", from_url_mock)
    monkeypatch.delenv("REDIS_URL", raising=False)

    generator = deps_module.get_redis()
    await generator.__anext__()
    await generator.aclose()

    from_url_mock.assert_called_once_with(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True,
    )


@pytest.mark.asyncio
async def test_get_auth_service_returns_auth_service(deps_module):
    auth_module = importlib.import_module("app.services.auth_services")
    auth_module = importlib.reload(auth_module)

    fake_db = object()
    fake_redis = object()

    service = await deps_module.get_auth_service(db=fake_db, redis_client=fake_redis)

    assert isinstance(service, auth_module.AuthService)
    assert service.db is fake_db
    assert service.redis_client is fake_redis


@pytest.mark.asyncio
async def test_get_current_user_raises_without_credentials(deps_module):
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(credentials=None, db=db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_for_invalid_token(monkeypatch, deps_module):
    db = AsyncMock()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")

    monkeypatch.setattr(deps_module, "_decode_access_token", lambda *_: None)

    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(credentials=credentials, db=db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_for_invalid_subject(monkeypatch, deps_module):
    db = AsyncMock()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    monkeypatch.setattr(
        deps_module,
        "_decode_access_token",
        lambda *_: {"sub": "not-a-uuid"},
    )

    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(credentials=credentials, db=db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_when_user_not_found(monkeypatch, deps_module):
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    user_id = uuid.uuid4()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    monkeypatch.setattr(
        deps_module,
        "_decode_access_token",
        lambda *_: {"sub": str(user_id)},
    )

    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(credentials=credentials, db=db)

    assert exc.value.status_code == 401
    db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_returns_user(monkeypatch, deps_module):
    user_id = uuid.uuid4()
    user = object()
    db = AsyncMock()
    db.get = AsyncMock(return_value=user)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    monkeypatch.setattr(
        deps_module,
        "_decode_access_token",
        lambda *_: {"sub": str(user_id)},
    )

    current_user = await deps_module.get_current_user(credentials=credentials, db=db)

    assert current_user is user
    db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_tenant_raises_for_unauthorized_membership(deps_module):
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)
    user = type("UserObj", (), {"id": uuid.uuid4()})()
    tenant_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_tenant(
            current_user=user,
            db=db,
            tenant_id=tenant_id,
        )

    assert exc.value.status_code == 403
    db.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_tenant_returns_tenant_for_member(deps_module):
    tenant = object()
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=tenant)
    user = type("UserObj", (), {"id": uuid.uuid4()})()
    tenant_id = uuid.uuid4()

    current_tenant = await deps_module.get_current_tenant(
        current_user=user,
        db=db,
        tenant_id=tenant_id,
    )

    assert current_tenant is tenant
    db.scalar.assert_awaited_once()
