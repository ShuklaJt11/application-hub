from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.models.application import Application
from app.models.tenant import Tenant
from app.repositories.reminder_repository import ReminderRepository


async def _create_tenant(db_session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _create_application(db_session, tenant_id, title: str) -> Application:
    application = Application(
        tenant_id=tenant_id,
        title=title,
        company="Contoso",
        location="Remote",
        applied_date=date(2026, 3, 1),
    )
    db_session.add(application)
    await db_session.flush()
    return application


@pytest.mark.asyncio
async def test_create_reminder_returns_persisted_model(db_session):
    tenant = await _create_tenant(db_session, "CreateReminderRepoTenant")
    application = await _create_application(db_session, tenant.id, "Role A")
    repo = ReminderRepository(db_session)

    created = await repo.create_reminder(
        {
            "tenant_id": tenant.id,
            "application_id": application.id,
            "remind_at": datetime.now(timezone.utc),
            "message": "Follow up",
        }
    )

    assert created.id is not None
    assert created.tenant_id == tenant.id
    assert created.application_id == application.id
    assert created.sent is False


@pytest.mark.asyncio
async def test_fetch_pending_reminders_applies_filters_and_tenant_scope(db_session):
    tenant = await _create_tenant(db_session, "PendingTenantA")
    another_tenant = await _create_tenant(db_session, "PendingTenantB")
    app_a = await _create_application(db_session, tenant.id, "Role A")
    app_b = await _create_application(db_session, another_tenant.id, "Role B")
    repo = ReminderRepository(db_session)

    now = datetime.now(timezone.utc)

    due_unsent = await repo.create_reminder(
        {
            "tenant_id": tenant.id,
            "application_id": app_a.id,
            "remind_at": now - timedelta(minutes=5),
            "message": "Due and unsent",
        }
    )
    await repo.create_reminder(
        {
            "tenant_id": tenant.id,
            "application_id": app_a.id,
            "remind_at": now + timedelta(minutes=5),
            "message": "Future reminder",
        }
    )
    sent_due = await repo.create_reminder(
        {
            "tenant_id": tenant.id,
            "application_id": app_a.id,
            "remind_at": now - timedelta(minutes=10),
            "message": "Already sent",
            "sent": True,
        }
    )
    await repo.create_reminder(
        {
            "tenant_id": another_tenant.id,
            "application_id": app_b.id,
            "remind_at": now - timedelta(minutes=1),
            "message": "Different tenant",
        }
    )

    pending = await repo.fetch_pending_reminders(tenant.id)
    pending_ids = {item.id for item in pending}

    assert due_unsent.id in pending_ids
    assert sent_due.id not in pending_ids
    assert len(pending_ids) == 1


@pytest.mark.asyncio
async def test_mark_sent_updates_flag_and_returns_none_when_missing(db_session):
    tenant = await _create_tenant(db_session, "MarkSentTenant")
    application = await _create_application(db_session, tenant.id, "Role C")
    repo = ReminderRepository(db_session)

    reminder = await repo.create_reminder(
        {
            "tenant_id": tenant.id,
            "application_id": application.id,
            "remind_at": datetime.now(timezone.utc),
            "message": "Mark me",
        }
    )

    updated = await repo.mark_sent(reminder.id)

    assert updated is not None
    assert updated.sent is True

    missing = await repo.mark_sent(UUID("00000000-0000-0000-0000-000000000000"))
    assert missing is None
