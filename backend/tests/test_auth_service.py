import importlib
import sys
import uuid
from unittest.mock import AsyncMock

import pytest

from app.schemas.auth import UserCreate, UserLogin


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
        self.begin_calls = 0

    async def scalar(self, _query):
        return self.scalar_result

    def begin(self):
        self.begin_calls += 1
        return _BeginContext()

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_calls += 1
        for obj in self.added:
            if hasattr(obj, "id") and getattr(obj, "id") is None:
                setattr(obj, "id", uuid.uuid4())


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
    assert db.begin_calls == 1
    assert db.flush_calls == 2
    assert len(db.added) == 3

    user = db.added[0]
    redis_client.setex.assert_awaited_once_with(
        f"{user.id}:token-id",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
        "refresh-token",
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
        f"{user_id}:token-id",
        auth_services_module.REFRESH_EXPIRE_MINUTES * 60,
        "refresh-token",
    )
