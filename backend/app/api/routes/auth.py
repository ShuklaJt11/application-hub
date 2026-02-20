from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service
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
    "/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    payload: UserCreate, service: Any = Depends(get_auth_service)
) -> TokenResponse:
    return await service.signup(payload)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: UserLogin, service: Any = Depends(get_auth_service)
) -> TokenResponse:
    return await service.login(payload)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    payload: RefreshTokenRequest, service: Any = Depends(get_auth_service)
) -> TokenResponse:
    return await service.refresh(payload)


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(
    payload: LogoutRequest, service: Any = Depends(get_auth_service)
) -> MessageResponse:
    return await service.logout(payload)
