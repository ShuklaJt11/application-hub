from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, rate_limit
from app.schemas.auth import (
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
