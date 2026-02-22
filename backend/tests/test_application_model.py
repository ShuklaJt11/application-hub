from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_create_application_sets_defaults(db_session):
    tenant = Tenant(name="Acme")
    db_session.add(tenant)
    await db_session.flush()

    application = Application(
        tenant_id=tenant.id,
        title="Software Engineer",
        company="Contoso",
        location="Remote",
        applied_date=date(2026, 2, 22),
    )
    db_session.add(application)
    await db_session.flush()
    await db_session.refresh(application)

    assert application.id is not None
    assert application.status == ApplicationStatus.applied
    assert application.created_at is not None
    assert application.updated_at is not None
    assert application.deleted_at is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing_field",
    ["title", "company", "location", "applied_date"],
)
async def test_application_required_fields_cannot_be_null(db_session, missing_field):
    tenant = Tenant(name="RequiredTenant")
    db_session.add(tenant)
    await db_session.flush()

    payload = {
        "tenant_id": tenant.id,
        "title": "Backend Engineer",
        "company": "Fabrikam",
        "location": "Bengaluru",
        "applied_date": date(2026, 2, 21),
    }
    payload[missing_field] = None

    db_session.add(Application(**payload))
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_application_relationship_back_populates_to_tenant(db_session):
    tenant = Tenant(name="RelTenant")
    db_session.add(tenant)
    await db_session.flush()

    application = Application(
        tenant_id=tenant.id,
        title="Data Engineer",
        company="Northwind",
        status=ApplicationStatus.screening,
        location="Hybrid",
        applied_date=date(2026, 2, 20),
    )
    db_session.add(application)
    await db_session.flush()

    stored_tenant = await db_session.scalar(
        select(Tenant)
        .options(selectinload(Tenant.applications))
        .where(Tenant.id == tenant.id)
    )

    assert stored_tenant is not None
    assert len(stored_tenant.applications) == 1
    assert stored_tenant.applications[0].id == application.id
    assert stored_tenant.applications[0].status == ApplicationStatus.screening


def test_application_status_enum_values_are_expected():
    assert [status.value for status in ApplicationStatus] == [
        "applied",
        "screening",
        "interview",
        "offer",
        "rejected",
    ]


def test_application_declares_expected_indexes():
    index_names = {index.name for index in Application.__table__.indexes}

    assert "ix_applications_tenant_id" in index_names
    assert "ix_applications_tenant_status" in index_names
    assert "ix_applications_tenant_company" in index_names
    assert "ix_applications_tenant_applied_date" in index_names
