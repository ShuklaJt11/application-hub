from collections.abc import Awaitable, Callable
from uuid import UUID

from app.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository


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
        if self.notifier is None:
            return
        await self.notifier(reminder)

    async def mark_reminder_sent(self, reminder_id: UUID) -> Reminder | None:
        return await self.repository.mark_sent(reminder_id)

    async def process_due_reminders(self, tenant_id: UUID) -> int:
        pending_reminders = await self.fetch_due_reminders(tenant_id)
        processed_count = 0

        for reminder in pending_reminders:
            try:
                await self.send_notification(reminder)
            except Exception:
                continue

            marked = await self.mark_reminder_sent(reminder.id)
            if marked is not None:
                processed_count += 1

        return processed_count
