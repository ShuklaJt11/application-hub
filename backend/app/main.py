import logging
import os
from contextlib import asynccontextmanager  # type: ignore[attr-defined]

import redis.asyncio as redis
from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,  # type: ignore[import-untyped]
)
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.api.router import api_router
from app.db.session import AsyncSessionLocal, engine
from app.repositories.reminder_repository import ReminderRepository
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = None
    scheduler: AsyncIOScheduler | None = None
    limiter_initialized = False

    try:
        redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            encoding="utf-8",
            decode_responses=True,
        )
        await FastAPILimiter.init(redis_client)
        limiter_initialized = True

        scheduler = AsyncIOScheduler()
        interval_seconds = int(os.getenv("REMINDER_CHECK_INTERVAL_SECONDS", "60"))

        async def _enqueue_due_reminders_job() -> None:
            async with AsyncSessionLocal() as session:
                service = ReminderService(
                    repository=ReminderRepository(session=session)
                )
                enqueued = await service.enqueue_due_reminders(redis_client)
                if enqueued:
                    logger.info("Enqueued %s due reminders", enqueued)

        async def _process_queue_job() -> None:
            async with AsyncSessionLocal() as session:
                service = ReminderService(
                    repository=ReminderRepository(session=session)
                )
                processed = await service.process_queued_reminders(redis_client)
                if processed:
                    logger.info("Processed %s queued reminders", processed)

        scheduler.add_job(
            _enqueue_due_reminders_job,
            trigger="interval",
            seconds=interval_seconds,
            id="enqueue_due_reminders",
            replace_existing=True,
        )
        scheduler.add_job(
            _process_queue_job,
            trigger="interval",
            seconds=interval_seconds,
            id="process_queued_reminders",
            replace_existing=True,
        )
        scheduler.start()
    except Exception:
        limiter_initialized = False
        logger.exception(
            "Rate limiter initialization failed. Requests will continue without it."
        )

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
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
