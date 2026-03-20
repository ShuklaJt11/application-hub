import logging
from collections.abc import Awaitable, Callable
from uuid import UUID

import redis.asyncio as redis

from app.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository

logger = logging.getLogger(__name__)
REMINDER_QUEUE_KEY = "reminders:queue"


class ReminderService:
    def __init__(
        self,
        repository: ReminderRepository,
        notifier: Callable[[Reminder], Awaitable[None]] | None = None,
    ):
        self.repository = repository
        self.notifier = notifier

    async def create_reminder(self, data: dict) -> Reminder:
        return await self.repository.create_reminder(data)

    async def fetch_due_reminders(self, tenant_id: UUID) -> list[Reminder]:
        return await self.repository.fetch_pending_reminders(tenant_id)

    async def send_notification(self, reminder: Reminder) -> None:
        if self.notifier is not None:
            await self.notifier(reminder)
            return

        logger.info(
            "Sending reminder : reminder_id=%s tenant_id=%s application_id=%s",
            reminder.id,
            reminder.tenant_id,
            reminder.application_id,
        )

    async def mark_reminder_sent(self, reminder_id: UUID) -> Reminder | None:
        return await self.repository.mark_sent(reminder_id)

    async def process_due_reminders(self, tenant_id: UUID) -> int:
        pending_reminders = await self.fetch_due_reminders(tenant_id)
        processed_count = 0

        for reminder in pending_reminders:
            try:
                await self.send_notification(reminder)
            except Exception:
                logger.exception(
                    "Failed to send due reminder reminder_id=%s tenant_id=%s",
                    reminder.id,
                    reminder.tenant_id,
                )
                continue

            marked = await self.mark_reminder_sent(reminder.id)
            if marked is not None:
                processed_count += 1

        return processed_count

    async def run_due_reminders_worker(self, tenant_id: UUID) -> int:
        return await self.process_due_reminders(tenant_id)

    async def enqueue_due_reminders(
        self,
        redis_client: redis.Redis,
        batch_size: int = 100,
    ) -> int:
        due_reminders = await self.repository.fetch_pending_reminders_global(
            limit=batch_size
        )
        if not due_reminders:
            return 0

        reminder_ids = [str(reminder.id) for reminder in due_reminders]
        await redis_client.rpush(REMINDER_QUEUE_KEY, *reminder_ids)
        logger.info("Queued %s reminders", len(reminder_ids))
        return len(reminder_ids)

    async def process_queued_reminders(
        self,
        redis_client: redis.Redis,
        max_items: int = 100,
    ) -> int:
        processed_count = 0

        for _ in range(max_items):
            reminder_id = await redis_client.lpop(REMINDER_QUEUE_KEY)
            if reminder_id is None:
                break

            try:
                reminder_uuid = UUID(reminder_id)
            except ValueError:
                logger.warning(
                    "Skipping invalid reminder id from queue: %s", reminder_id
                )
                continue

            reminder = await self.repository.get_by_id(reminder_uuid)
            if reminder is None or reminder.sent:
                continue

            try:
                await self.send_notification(reminder)
            except Exception:
                logger.exception(
                    "Failed to process queued reminder reminder_id=%s tenant_id=%s",
                    reminder.id,
                    reminder.tenant_id,
                )
                continue

            marked = await self.mark_reminder_sent(reminder.id)
            if marked is not None:
                processed_count += 1

        if processed_count:
            logger.info("Processed %s queued reminders in worker", processed_count)

        return processed_count
