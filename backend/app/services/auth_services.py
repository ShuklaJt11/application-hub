import redis.asyncio as redis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    REFRESH_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.tenant_user import TenantRole, TenantUser
from app.models.user import User
from app.schemas.auth import (
    ActiveSessionsResponse,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
)


class AuthService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client

    @staticmethod
    def _refresh_key(user_id: str, token_id: str) -> str:
        return f"refresh:{user_id}:{token_id}"

    @staticmethod
    def _refresh_index_key(user_id: str) -> str:
        return f"refresh_index:{user_id}"

    async def _store_refresh_token(
        self, user_id: str, token_id: str, token: str
    ) -> None:
        ttl_seconds = REFRESH_EXPIRE_MINUTES * 60
        key = self._refresh_key(user_id, token_id)
        index_key = self._refresh_index_key(user_id)

        await self.redis_client.setex(key, ttl_seconds, hash_token(token))
        await self.redis_client.sadd(index_key, token_id)
        await self.redis_client.expire(index_key, ttl_seconds)

    async def _revoke_refresh_token(self, user_id: str, token_id: str) -> int:
        key = self._refresh_key(user_id, token_id)
        index_key = self._refresh_index_key(user_id)
        deleted = await self.redis_client.delete(key)
        await self.redis_client.srem(index_key, token_id)
        return int(deleted)

    async def _revoke_all_refresh_tokens(
        self, user_id: str, current_token_id: str | None = None
    ) -> None:
        index_key = self._refresh_index_key(user_id)
        token_ids = await self.redis_client.smembers(index_key)
        if token_ids:
            # Keep delete ordering deterministic while prioritizing the current token.
            ordered_token_ids: list[str] = []
            if current_token_id and current_token_id in token_ids:
                ordered_token_ids.append(current_token_id)

            remaining_token_ids = sorted(
                token_id for token_id in token_ids if token_id != current_token_id
            )
            ordered_token_ids.extend(remaining_token_ids)

            keys = [
                self._refresh_key(user_id, token_id) for token_id in ordered_token_ids
            ]
            await self.redis_client.delete(*keys)
        await self.redis_client.delete(index_key)

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

        await self._store_refresh_token(str(user.id), token_id, refresh_token)

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

        await self._store_refresh_token(str(user.id), token_id, refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        token_payload = decode_token(payload.refresh_token, "refresh")
        if token_payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        sub = token_payload.get("sub")
        token_id = token_payload.get("jti")
        if not isinstance(sub, str) or not isinstance(token_id, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        redis_key = self._refresh_key(sub, token_id)
        stored_refresh_token_hash = await self.redis_client.get(redis_key)
        presented_token_hash = hash_token(payload.refresh_token)

        if stored_refresh_token_hash is None:
            # A structurally valid token that is missing from Redis
            # is likely replayed/revoked.
            await self._revoke_all_refresh_tokens(sub, current_token_id=token_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected. Please log in again.",
            )

        if stored_refresh_token_hash != presented_token_hash:
            await self._revoke_all_refresh_tokens(sub, current_token_id=token_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected. Please log in again.",
            )

        await self._revoke_refresh_token(sub, token_id)

        access_token = create_access_token(sub)
        new_refresh_token, new_token_id = create_refresh_token(sub)
        await self._store_refresh_token(sub, new_token_id, new_refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def logout(self, payload: LogoutRequest) -> MessageResponse:
        token_payload = decode_token(payload.refresh_token, "refresh")
        if token_payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        sub = token_payload.get("sub")
        token_id = token_payload.get("jti")
        if not isinstance(sub, str) or not isinstance(token_id, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        deleted = await self._revoke_refresh_token(sub, token_id)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or not found",
            )

        return MessageResponse(message="Logged out successfully")

    async def _get_user_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email))

    async def list_active_sessions(self, user_id: str) -> ActiveSessionsResponse:
        token_ids = await self.redis_client.smembers(self._refresh_index_key(user_id))
        sessions = sorted(token_ids)
        return ActiveSessionsResponse(sessions=sessions, count=len(sessions))

    async def revoke_session(self, user_id: str, token_id: str) -> MessageResponse:
        deleted = await self._revoke_refresh_token(user_id, token_id)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return MessageResponse(message="Session revoked successfully")
