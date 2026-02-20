import pytest
from pydantic import ValidationError

from app.schemas.auth import TokenPayload, TokenResponse


def test_token_response_valid_and_default_refresh_none():
    obj = TokenResponse(access_token="a.b.c", token_type="bearer")
    assert obj.access_token == "a.b.c"
    assert obj.refresh_token is None
    assert obj.token_type == "bearer"


def test_token_response_rejects_invalid_token_type():
    with pytest.raises(ValidationError):
        TokenResponse(
            access_token="a.b.c", token_type="Bearer"
        )  # must be lowercase literal


def test_token_payload_valid_access():
    obj = TokenPayload(sub="user-id", type="access", exp=1_700_000_000)
    assert obj.jti is None


def test_token_payload_valid_refresh_with_jti():
    obj = TokenPayload(sub="user-id", type="refresh", exp=1_700_000_000, jti="uuid-ish")
    assert obj.jti == "uuid-ish"


def test_token_payload_rejects_invalid_type():
    with pytest.raises(ValidationError):
        TokenPayload(sub="user-id", type="id", exp=1_700_000_000)
