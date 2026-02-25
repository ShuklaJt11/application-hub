from fastapi import APIRouter

from app.api.routes.applications import router as applications_router
from app.api.routes.auth import router as auth_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(applications_router)
