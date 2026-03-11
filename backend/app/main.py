import logging
import os
from contextlib import asynccontextmanager  # type: ignore[attr-defined]

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.api.router import api_router
from app.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = None
    limiter_initialized = False

    try:
        redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            encoding="utf-8",
            decode_responses=True,
        )
        await FastAPILimiter.init(redis_client)
        limiter_initialized = True
    except Exception:
        limiter_initialized = False
        logger.exception(
            "Rate limiter initialization failed. Requests will continue without it."
        )

    try:
        yield
    finally:
        if redis_client is not None and limiter_initialized:
            await FastAPILimiter.close()
        if redis_client is not None:
            await redis_client.close()
        await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Backend is running"}
