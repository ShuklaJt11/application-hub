from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.reminder import Reminder
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_create_reminder_sets_defaults(db_session):
    tenant = Tenant(name="ReminderTenant")
    db_session.add(tenant)
    await db_session.flush()

    application = Application(
        tenant_id=tenant.id,
        title="SWE",
        company="Contoso",
        location="Remote",
        applied_date=date(2026, 3, 1),
    )
    db_session.add(application)
    await db_session.flush()

    reminder = Reminder(
        tenant_id=tenant.id,
        application_id=application.id,
        remind_at=datetime(2026, 3, 20, 8, 30, tzinfo=timezone.utc),
    )
    db_session.add(reminder)
    await db_session.flush()
    await db_session.refresh(reminder)

    assert reminder.id is not None
    assert reminder.sent is False
    assert reminder.message is None
    assert reminder.created_at is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_field", ["tenant_id", "application_id", "remind_at"])
async def test_reminder_required_fields_cannot_be_null(db_session, missing_field):
    tenant = Tenant(name="ReminderRequiredTenant")
    db_session.add(tenant)
    await db_session.flush()

    application = Application(
        tenant_id=tenant.id,
        title="Backend Engineer",
        company="Fabrikam",
        location="Onsite",
        applied_date=date(2026, 3, 2),
    )
    db_session.add(application)
    await db_session.flush()

    payload = {
        "tenant_id": tenant.id,
        "application_id": application.id,
        "remind_at": datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc),
        "message": "Follow up",
    }
    payload[missing_field] = None

    db_session.add(Reminder(**payload))
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_reminder_relationship_back_populates_to_application(db_session):
    tenant = Tenant(name="ReminderRelTenant")
    db_session.add(tenant)
    await db_session.flush()

    application = Application(
        tenant_id=tenant.id,
        title="Data Engineer",
        company="Northwind",
        location="Hybrid",
        applied_date=date(2026, 3, 3),
    )
    db_session.add(application)
    await db_session.flush()

    reminder = Reminder(
        tenant_id=tenant.id,
        application_id=application.id,
        remind_at=datetime(2026, 3, 22, 10, 0, tzinfo=timezone.utc),
        message="Check status",
    )
    db_session.add(reminder)
    await db_session.flush()

    stored_application = await db_session.scalar(
        select(Application)
        .options(selectinload(Application.reminders))
        .where(Application.id == application.id)
    )

    stored_reminder = await db_session.scalar(
        select(Reminder)
        .options(selectinload(Reminder.application))
        .where(Reminder.id == reminder.id)
    )

    assert stored_application is not None
    assert len(stored_application.reminders) == 1
    assert stored_application.reminders[0].id == reminder.id

    assert stored_reminder is not None
    assert stored_reminder.application.id == application.id
