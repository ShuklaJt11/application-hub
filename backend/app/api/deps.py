import os
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import redis.asyncio as redis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

if TYPE_CHECKING:
    from app.services.auth_services import AuthService


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
