import redis.asyncio as redis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    REFRESH_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.tenant_user import TenantRole, TenantUser
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin


class AuthService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client

    async def signup(self, payload: UserCreate) -> TokenResponse:
        existing = await self._get_user_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        hashed = hash_password(payload.password.get_secret_value())

        async with self.db.begin():
            user = User(
                email=payload.email,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                hashed_password=hashed,
            )
            self.db.add(user)
            await self.db.flush()

            tenant = Tenant(name=f"{payload.username}'s Workspace")
            self.db.add(tenant)
            await self.db.flush()

            self.db.add(
                TenantUser(user_id=user.id, tenant_id=tenant.id, role=TenantRole.admin)
            )

            access_token = create_access_token(str(user.id))
            refresh_token, token_id = create_refresh_token(str(user.id))

        await self.redis_client.setex(
            f"{user.id}:{token_id}", REFRESH_EXPIRE_MINUTES * 60, refresh_token
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def login(self, payload: UserLogin) -> TokenResponse:
        user = await self._get_user_by_email(payload.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            payload.password.get_secret_value(), user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(str(user.id))
        refresh_token, token_id = create_refresh_token(str(user.id))

        await self.redis_client.setex(
            f"{user.id}:{token_id}",
            REFRESH_EXPIRE_MINUTES * 60,
            refresh_token,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def _get_user_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email))
