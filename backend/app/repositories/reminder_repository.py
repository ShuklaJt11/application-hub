from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder


class ReminderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_reminder(self, data: dict) -> Reminder:
        reminder = Reminder(**data)
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def fetch_pending_reminders(self, tenant_id: UUID) -> list[Reminder]:
        now = datetime.now(timezone.utc)
        query = (
            select(Reminder)
            .where(
                Reminder.tenant_id == tenant_id,
                Reminder.sent.is_(False),
                Reminder.remind_at <= now,
            )
            .order_by(Reminder.remind_at.asc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def fetch_pending_reminders_global(self, limit: int = 100) -> list[Reminder]:
        now = datetime.now(timezone.utc)
        query = (
            select(Reminder)
            .where(
                Reminder.sent.is_(False),
                Reminder.remind_at <= now,
            )
            .order_by(Reminder.remind_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, reminder_id: UUID) -> Reminder | None:
        result = await self.session.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        return result.scalar_one_or_none()

    async def mark_sent(self, reminder_id: UUID) -> Reminder | None:
        reminder = await self.get_by_id(reminder_id)
        if reminder is None:
            return None

        reminder.sent = True
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder
