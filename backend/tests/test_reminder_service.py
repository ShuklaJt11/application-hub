import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.reminder import Reminder
from app.services.reminder_service import ReminderService


def _make_reminder() -> Reminder:
    return Reminder(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        application_id=uuid.uuid4(),
        remind_at=datetime.now(timezone.utc),
        message="Follow up",
    )


@pytest.mark.asyncio
async def test_create_reminder_calls_repository():
    repository = AsyncMock()
    reminder = _make_reminder()
    repository.create_reminder = AsyncMock(return_value=reminder)
    service = ReminderService(repository=repository)

    payload = {
        "tenant_id": reminder.tenant_id,
        "application_id": reminder.application_id,
        "remind_at": reminder.remind_at,
        "message": reminder.message,
    }

    created = await service.create_reminder(payload)

    assert created == reminder
    repository.create_reminder.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_process_due_reminders_fetches_notifies_and_marks_sent():
    repository = AsyncMock()
    reminder_1 = _make_reminder()
    reminder_2 = _make_reminder()
    repository.fetch_pending_reminders = AsyncMock(
        return_value=[reminder_1, reminder_2]
    )
    repository.mark_sent = AsyncMock(side_effect=[reminder_1, reminder_2])

    notifier = AsyncMock()
    service = ReminderService(repository=repository, notifier=notifier)

    tenant_id = uuid.uuid4()
    processed = await service.process_due_reminders(tenant_id)

    assert processed == 2
    repository.fetch_pending_reminders.assert_awaited_once_with(tenant_id)
    notifier.assert_any_await(reminder_1)
    notifier.assert_any_await(reminder_2)
    assert notifier.await_count == 2
    repository.mark_sent.assert_any_await(reminder_1.id)
    repository.mark_sent.assert_any_await(reminder_2.id)
    assert repository.mark_sent.await_count == 2


@pytest.mark.asyncio
async def test_process_due_reminders_skips_mark_when_notification_fails():
    repository = AsyncMock()
    reminder_1 = _make_reminder()
    reminder_2 = _make_reminder()
    repository.fetch_pending_reminders = AsyncMock(
        return_value=[reminder_1, reminder_2]
    )
    repository.mark_sent = AsyncMock(return_value=reminder_2)

    notifier = AsyncMock(side_effect=[RuntimeError("smtp error"), None])
    service = ReminderService(repository=repository, notifier=notifier)

    processed = await service.process_due_reminders(uuid.uuid4())

    assert processed == 1
    repository.mark_sent.assert_awaited_once_with(reminder_2.id)


@pytest.mark.asyncio
async def test_run_due_reminders_worker_delegates_to_process_due_reminders():
    repository = AsyncMock()
    service = ReminderService(repository=repository)
    service.process_due_reminders = AsyncMock(return_value=3)

    tenant_id = uuid.uuid4()
    processed = await service.run_due_reminders_worker(tenant_id)

    assert processed == 3
    service.process_due_reminders.assert_awaited_once_with(tenant_id)


@pytest.mark.asyncio
async def test_send_notification_without_notifier_does_not_raise():
    repository = AsyncMock()
    reminder = _make_reminder()
    service = ReminderService(repository=repository, notifier=None)

    await service.send_notification(reminder)
