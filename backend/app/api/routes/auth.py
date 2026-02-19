from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service
from app.schemas.auth import TokenResponse, UserCreate, UserLogin

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
