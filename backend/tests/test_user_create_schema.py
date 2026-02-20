import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate


def test_user_create_normalizes_email_and_username():
    obj = UserCreate(
        email="  USER@Example.COM ",
        username="  JohnDoe  ",
        first_name="John",
        last_name="Doe",
        password="supersecret123",
    )
    assert obj.email == "user@example.com"
    assert obj.username == "johndoe"


def test_user_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        UserCreate(
            email="user@example.com",
            username="john",
            first_name="John",
            last_name="Doe",
            password="supersecret123",
            role="admin",  # extra field
        )


@pytest.mark.parametrize(
    "payload",
    [
        dict(
            email="bad-email",
            username="john",
            first_name="John",
            last_name="Doe",
            password="supersecret123",
        ),
        dict(
            email="u@example.com",
            username="ab",
            first_name="John",
            last_name="Doe",
            password="supersecret123",
        ),
        dict(
            email="u@example.com",
            username="john",
            first_name="",
            last_name="Doe",
            password="supersecret123",
        ),
        dict(
            email="u@example.com",
            username="john",
            first_name="John",
            last_name="Doe",
            password="short",
        ),
    ],
)
def test_user_create_invalid_payloads(payload):
    with pytest.raises(ValidationError):
        UserCreate(**payload)
