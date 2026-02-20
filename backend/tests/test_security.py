import importlib
import sys
from datetime import timedelta

import pytest


@pytest.fixture
def security(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_SECRET", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_EXPIRE_MINUTES", "1440")

    sys.modules.pop("app.core.security", None)
    return importlib.import_module("app.core.security")


def test_hash_password_and_verify_success(security):
    plain = "MySecurePass123!"
    hashed = security.hash_password(plain)

    assert hashed != plain
    assert security.verify_password(plain, hashed) is True


def test_verify_password_fails_for_wrong_password(security):
    hashed = security.hash_password("CorrectPass123!")
    assert security.verify_password("WrongPass123!", hashed) is False


def test_create_access_token_and_decode(security):
    token = security.create_access_token("user-1")
    payload = security.decode_token(token, "access")

    assert payload is not None
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"


def test_create_refresh_token_includes_jti_and_decode(security):
    token, jti = security.create_refresh_token("user-2")
    payload = security.decode_token(token, "refresh")

    assert payload is not None
    assert payload["sub"] == "user-2"
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti


def test_refresh_jti_is_unique(security):
    _, jti1 = security.create_refresh_token("user-3")
    _, jti2 = security.create_refresh_token("user-3")

    assert jti1 != jti2


def test_decode_token_returns_none_for_wrong_token_type(security):
    token = security.create_access_token("user-4")
    assert security.decode_token(token, "refresh") is None


def test_decode_token_returns_none_for_expired_token(security):
    expired_token = security._create_token(
        security.ACCESS_SECRET,
        "user-5",
        timedelta(seconds=-1),
        "access",
    )
    assert security.decode_token(expired_token, "access") is None


def test_decode_token_returns_none_for_malformed_token(security):
    assert security.decode_token("not-a-jwt-token", "access") is None


def test_get_required_env_raises_for_missing_variable(security, monkeypatch):
    monkeypatch.delenv("JWT_MISSING", raising=False)
    with pytest.raises(RuntimeError):
        security._get_required_env("JWT_MISSING")


def test_decode_token_returns_none_for_invalid_token_type_input(security):
    token = security.create_access_token("user-6")
    assert security.decode_token(token, "invalid-type") is None
