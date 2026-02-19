import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


ACCESS_SECRET = _get_required_env("JWT_ACCESS_SECRET")
REFRESH_SECRET = _get_required_env("JWT_REFRESH_SECRET")
ALGORITHM = _get_required_env("JWT_ALGORITHM")
ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", 15))
REFRESH_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_EXPIRE_MINUTES", 1440))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    secret: str,
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    jti: str | None = None,
) -> str:
    expiry = datetime.now(timezone.utc) + expires_delta

    payload = {"sub": subject, "type": token_type, "exp": expiry}

    if jti is not None:
        payload["jti"] = jti

    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(
        ACCESS_SECRET, subject, timedelta(minutes=ACCESS_EXPIRE_MINUTES), "access"
    )


def create_refresh_token(subject: str) -> tuple[str, str]:
    jti = str(uuid4())
    token = _create_token(
        REFRESH_SECRET,
        subject,
        timedelta(minutes=REFRESH_EXPIRE_MINUTES),
        "refresh",
        jti,
    )
    return token, jti


def decode_token(token: str, token_type: str) -> dict[str, Any] | None:
    secret_map = {"access": ACCESS_SECRET, "refresh": REFRESH_SECRET}
    secret = secret_map.get(token_type)
    if secret is None:
        return None

    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        if "sub" not in payload:
            return None

        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
