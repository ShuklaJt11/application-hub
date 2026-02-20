from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.api.routes.auth import router as auth_router


def _build_test_client(fake_service):
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    return TestClient(app)


def test_signup_route_calls_service_and_returns_tokens():
    fake_service = AsyncMock()
    fake_service.signup.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    client = _build_test_client(fake_service)

    response = client.post(
        "/auth/signup",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    fake_service.signup.assert_awaited_once()


def test_login_route_calls_service_and_returns_tokens():
    fake_service = AsyncMock()
    fake_service.login.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    client = _build_test_client(fake_service)

    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    fake_service.login.assert_awaited_once()


def test_refresh_route_calls_service_and_returns_tokens():
    fake_service = AsyncMock()
    fake_service.refresh.return_value = {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }
    client = _build_test_client(fake_service)

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "old-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }
    fake_service.refresh.assert_awaited_once()


def test_logout_route_calls_service_and_returns_message():
    fake_service = AsyncMock()
    fake_service.logout.return_value = {"message": "Logged out successfully"}
    client = _build_test_client(fake_service)

    response = client.post(
        "/auth/logout",
        json={"refresh_token": "refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
    fake_service.logout.assert_awaited_once()
