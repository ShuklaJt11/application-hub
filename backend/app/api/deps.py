import os
import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.tenant_user import TenantUser
from app.models.user import User

if TYPE_CHECKING:
    from app.services.auth_services import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_access_token(token: str) -> dict[str, object] | None:
    from app.core.security import decode_token

    return decode_token(token, "access")


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.close()


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> "AuthService":
    from app.services.auth_services import AuthService

    return AuthService(db=db, redis_client=redis_client)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    payload = _decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Header(alias="X-Tenant-ID"),
) -> Tenant:

    tenant = await db.scalar(
        select(Tenant)
        .join(TenantUser, Tenant.id == TenantUser.tenant_id)
        .where(
            and_(
                TenantUser.user_id == current_user.id,
                Tenant.id == tenant_id,
            )
        )
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to the specified tenant",
        )

    return tenant
