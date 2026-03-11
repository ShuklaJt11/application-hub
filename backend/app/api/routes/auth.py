from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user, rate_limit
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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(times=5, seconds=60)],
)
async def signup(
    payload: UserCreate, service: Any = Depends(get_auth_service)
) -> TokenResponse:
    return await service.signup(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[rate_limit(times=5, seconds=60)],
)
async def login(
    payload: UserLogin, service: Any = Depends(get_auth_service)
) -> TokenResponse:
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[rate_limit(times=20, seconds=60)],
)
async def refresh(
    payload: RefreshTokenRequest, service: Any = Depends(get_auth_service)
) -> TokenResponse:
    return await service.refresh(payload)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[rate_limit(times=30, seconds=60)],
)
async def logout(
    payload: LogoutRequest, service: Any = Depends(get_auth_service)
) -> MessageResponse:
    return await service.logout(payload)


@router.get(
    "/sessions",
    response_model=ActiveSessionsResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[rate_limit(times=30, seconds=60)],
)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_auth_service),
) -> ActiveSessionsResponse:
    return await service.list_active_sessions(str(current_user.id))


@router.delete(
    "/sessions/{token_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[rate_limit(times=30, seconds=60)],
)
async def revoke_session(
    token_id: str,
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_auth_service),
) -> MessageResponse:
    return await service.revoke_session(str(current_user.id), token_id)
