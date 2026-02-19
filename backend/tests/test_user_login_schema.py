import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin


def test_user_login_normalizes_email():
    obj = UserLogin(email="  USER@Example.COM  ", password="supersecret123")
    assert obj.email == "user@example.com"


def test_user_login_rejects_extra_fields():
    with pytest.raises(ValidationError):
        UserLogin(email="u@example.com", password="supersecret123", remember_me=True)


@pytest.mark.parametrize(
    "email,password",
    [
        ("bad-email", "supersecret123"),
        ("u@example.com", "short"),
    ],
)
def test_user_login_invalid_values(email, password):
    with pytest.raises(ValidationError):
        UserLogin(email=email, password=password)
