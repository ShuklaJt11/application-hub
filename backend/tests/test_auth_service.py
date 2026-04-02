import importlib
import sys
import uuid
from unittest.mock import AsyncMock

import pytest

from app.schemas.auth import LogoutRequest, RefreshTokenRequest, UserCreate, UserLogin


class _BeginContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDB:
    def __init__(self, scalar_result=None):
        self.scalar_result = scalar_result
        self.added = []
        self.flush_calls = 0
        self.commit_calls = 0

    async def scalar(self, _query):
        return self.scalar_result

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_calls += 1
        for obj in self.added:
            if hasattr(obj, "id") and getattr(obj, "id") is None:
                setattr(obj, "id", uuid.uuid4())

    async def commit(self):
        self.commit_calls += 1


@pytest.fixture
def auth_services_module(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_SECRET", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_EXPIRE_MINUTES", "1440")

    sys.modules.pop("app.core.security", None)
    sys.modules.pop("app.services.auth_services", None)
    return importlib.import_module("app.services.auth_services")


@pytest.mark.asyncio
async def test_signup_rejects_existing_email(auth_services_module):
    db = _FakeDB(scalar_result=object())
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    payload = UserCreate(
        email="existing@example.com",
        username="existinguser",
        first_name="Existing",
        last_name="User",
        password="StrongPass123!",
    )

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.signup(payload)

    assert exc.value.status_code == 409
    redis_client.setex.assert_not_called()


@pytest.mark.asyncio
async def test_signup_creates_user_tenant_and_refresh(
    auth_services_module, monkeypatch
):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    monkeypatch.setattr(auth_services_module, "hash_password", lambda _: "hashed-value")
    monkeypatch.setattr(
        auth_services_module, "create_access_token", lambda _: "access-token"
    )
    monkeypatch.setattr(
        auth_services_module,
        "create_refresh_token",
        lambda _: ("refresh-token", "token-id"),
    )

    payload = UserCreate(
        email="new@example.com",
        username="newuser",
        first_name="New",
        last_name="User",
        password="StrongPass123!",
    )

    response = await service.signup(payload)

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    assert response.token_type == "bearer"
    assert db.commit_calls == 1
    assert db.flush_calls == 2
    assert len(db.added) == 3

    user = db.added[0]
    redis_client.setex.assert_awaited_once_with(
        f"refresh:{user.id}:token-id",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
        auth_services_module.hash_token("refresh-token"),
    )
    redis_client.sadd.assert_awaited_once_with(f"refresh_index:{user.id}", "token-id")
    redis_client.expire.assert_awaited_once_with(
        f"refresh_index:{user.id}",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
    )


@pytest.mark.asyncio
async def test_login_rejects_unknown_email(auth_services_module):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    payload = UserLogin(email="missing@example.com", password="StrongPass123!")

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.login(payload)

    assert exc.value.status_code == 401
    redis_client.setex.assert_not_called()


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(auth_services_module, monkeypatch):
    user = type("UserObj", (), {"id": uuid.uuid4(), "hashed_password": "stored-hash"})()
    db = _FakeDB(scalar_result=user)
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    monkeypatch.setattr(auth_services_module, "verify_password", lambda *_: False)

    payload = UserLogin(email="user@example.com", password="WrongPass123!")

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.login(payload)

    assert exc.value.status_code == 401
    redis_client.setex.assert_not_called()


@pytest.mark.asyncio
async def test_login_returns_tokens_and_stores_refresh(
    auth_services_module, monkeypatch
):
    user_id = uuid.uuid4()
    user = type("UserObj", (), {"id": user_id, "hashed_password": "stored-hash"})()
    db = _FakeDB(scalar_result=user)
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    monkeypatch.setattr(auth_services_module, "verify_password", lambda *_: True)
    monkeypatch.setattr(
        auth_services_module, "create_access_token", lambda _: "access-token"
    )
    monkeypatch.setattr(
        auth_services_module,
        "create_refresh_token",
        lambda _: ("refresh-token", "token-id"),
    )

    payload = UserLogin(email="user@example.com", password="StrongPass123!")
    response = await service.login(payload)

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    assert response.token_type == "bearer"
    redis_client.setex.assert_awaited_once_with(
        f"refresh:{user_id}:token-id",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
        auth_services_module.hash_token("refresh-token"),
    )
    redis_client.sadd.assert_awaited_once_with(f"refresh_index:{user_id}", "token-id")
    redis_client.expire.assert_awaited_once_with(
        f"refresh_index:{user_id}",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
    )


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_refresh_token(auth_services_module, monkeypatch):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    monkeypatch.setattr(auth_services_module, "decode_token", lambda *_: None)

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.refresh(RefreshTokenRequest(refresh_token="bad-token"))

    assert exc.value.status_code == 401
    redis_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_rejects_when_token_not_in_redis(
    auth_services_module, monkeypatch
):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)
    redis_client.smembers = AsyncMock(return_value={"old-jti", "other-jti"})
    redis_client.delete = AsyncMock(return_value=1)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    monkeypatch.setattr(
        auth_services_module,
        "decode_token",
        lambda *_: {"sub": user_id, "jti": "old-jti"},
    )

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.refresh(RefreshTokenRequest(refresh_token="refresh-token"))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh token reuse detected. Please log in again."
    redis_client.get.assert_awaited_once_with(f"refresh:{user_id}:old-jti")
    redis_client.smembers.assert_awaited_once_with(f"refresh_index:{user_id}")
    redis_client.delete.assert_any_await(
        f"refresh:{user_id}:old-jti", f"refresh:{user_id}:other-jti"
    )
    redis_client.delete.assert_any_await(f"refresh_index:{user_id}")


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(auth_services_module, monkeypatch):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(
        return_value=auth_services_module.hash_token("old-refresh-token")
    )
    redis_client.delete = AsyncMock(return_value=1)
    redis_client.srem = AsyncMock(return_value=1)
    redis_client.sadd = AsyncMock(return_value=1)
    redis_client.expire = AsyncMock(return_value=1)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    monkeypatch.setattr(
        auth_services_module,
        "decode_token",
        lambda *_: {"sub": user_id, "jti": "old-jti"},
    )
    monkeypatch.setattr(
        auth_services_module, "create_access_token", lambda *_: "new-access"
    )
    monkeypatch.setattr(
        auth_services_module,
        "create_refresh_token",
        lambda *_: ("new-refresh", "new-jti"),
    )

    response = await service.refresh(
        RefreshTokenRequest(refresh_token="old-refresh-token")
    )

    assert response.access_token == "new-access"
    assert response.refresh_token == "new-refresh"
    assert response.token_type == "bearer"
    redis_client.get.assert_awaited_once_with(f"refresh:{user_id}:old-jti")
    redis_client.delete.assert_any_await(f"refresh:{user_id}:old-jti")
    redis_client.srem.assert_awaited_once_with(f"refresh_index:{user_id}", "old-jti")
    redis_client.setex.assert_awaited_once_with(
        f"refresh:{user_id}:new-jti",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
        auth_services_module.hash_token("new-refresh"),
    )
    redis_client.sadd.assert_awaited_once_with(f"refresh_index:{user_id}", "new-jti")
    redis_client.expire.assert_awaited_once_with(
        f"refresh_index:{user_id}",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
    )


@pytest.mark.asyncio
async def test_refresh_rejects_hash_mismatch_and_revokes_all(
    auth_services_module, monkeypatch
):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value="unexpected-hash")
    redis_client.smembers = AsyncMock(return_value={"old-jti", "newer-jti"})
    redis_client.delete = AsyncMock(return_value=1)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    monkeypatch.setattr(
        auth_services_module,
        "decode_token",
        lambda *_: {"sub": user_id, "jti": "old-jti"},
    )

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.refresh(RefreshTokenRequest(refresh_token="old-refresh-token"))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Refresh token reuse detected. Please log in again."
    redis_client.smembers.assert_awaited_once_with(f"refresh_index:{user_id}")
    redis_client.delete.assert_any_await(
        f"refresh:{user_id}:old-jti", f"refresh:{user_id}:newer-jti"
    )
    redis_client.delete.assert_any_await(f"refresh_index:{user_id}")


@pytest.mark.asyncio
async def test_logout_rejects_invalid_refresh_token(auth_services_module, monkeypatch):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    monkeypatch.setattr(auth_services_module, "decode_token", lambda *_: None)

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.logout(LogoutRequest(refresh_token="bad-token"))

    assert exc.value.status_code == 401
    redis_client.delete.assert_not_called()


@pytest.mark.asyncio
async def test_logout_rejects_missing_refresh_token_key(
    auth_services_module, monkeypatch
):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.delete = AsyncMock(return_value=0)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    monkeypatch.setattr(
        auth_services_module,
        "decode_token",
        lambda *_: {"sub": user_id, "jti": "old-jti"},
    )

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.logout(LogoutRequest(refresh_token="refresh-token"))

    assert exc.value.status_code == 401
    redis_client.delete.assert_awaited_once_with(f"refresh:{user_id}:old-jti")
    redis_client.srem.assert_awaited_once_with(f"refresh_index:{user_id}", "old-jti")


@pytest.mark.asyncio
async def test_logout_deletes_refresh_token_key(auth_services_module, monkeypatch):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.delete = AsyncMock(return_value=1)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    monkeypatch.setattr(
        auth_services_module,
        "decode_token",
        lambda *_: {"sub": user_id, "jti": "old-jti"},
    )

    response = await service.logout(LogoutRequest(refresh_token="refresh-token"))

    assert response.message == "Logged out successfully"
    redis_client.delete.assert_awaited_once_with(f"refresh:{user_id}:old-jti")
    redis_client.srem.assert_awaited_once_with(f"refresh_index:{user_id}", "old-jti")


@pytest.mark.asyncio
async def test_list_active_sessions_returns_sorted_token_ids(auth_services_module):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.smembers = AsyncMock(return_value={"jti-b", "jti-a", "jti-c"})
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    response = await service.list_active_sessions(user_id)

    assert response.count == 3
    assert response.sessions == ["jti-a", "jti-b", "jti-c"]
    redis_client.smembers.assert_awaited_once_with(f"refresh_index:{user_id}")


@pytest.mark.asyncio
async def test_revoke_session_returns_not_found_when_missing(auth_services_module):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.delete = AsyncMock(return_value=0)
    redis_client.srem = AsyncMock(return_value=0)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())

    with pytest.raises(auth_services_module.HTTPException) as exc:
        await service.revoke_session(user_id, "missing-jti")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Session not found"


@pytest.mark.asyncio
async def test_revoke_session_deletes_existing_session(auth_services_module):
    db = _FakeDB(scalar_result=None)
    redis_client = AsyncMock()
    redis_client.delete = AsyncMock(return_value=1)
    redis_client.srem = AsyncMock(return_value=1)
    service = auth_services_module.AuthService(db=db, redis_client=redis_client)

    user_id = str(uuid.uuid4())
    response = await service.revoke_session(user_id, "active-jti")

    assert response.message == "Session revoked successfully"
    redis_client.delete.assert_awaited_once_with(f"refresh:{user_id}:active-jti")
    redis_client.srem.assert_awaited_once_with(f"refresh_index:{user_id}", "active-jti")
