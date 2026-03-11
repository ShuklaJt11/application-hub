from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.application import Application, ApplicationStatus
from app.models.tenant import Tenant
from app.repositories.application_repository import ApplicationRepository


async def _create_tenant(db_session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.mark.asyncio
async def test_create_application_returns_persisted_model(db_session):
    tenant = await _create_tenant(db_session, "CreateRepoTenant")
    repo = ApplicationRepository(db_session)

    created = await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Backend Engineer",
            "company": "Contoso",
            "location": "Remote",
            "applied_date": date(2026, 2, 20),
        }
    )

    assert created.id is not None
    assert created.status == ApplicationStatus.applied

    stored = await db_session.scalar(
        select(Application).where(Application.id == created.id)
    )
    assert stored is not None


@pytest.mark.asyncio
async def test_get_application_by_id_is_tenant_scoped_and_returns_none(db_session):
    tenant = await _create_tenant(db_session, "TenantA")
    another_tenant = await _create_tenant(db_session, "TenantB")
    repo = ApplicationRepository(db_session)

    app_obj = await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "SDE",
            "company": "Northwind",
            "location": "Hybrid",
            "applied_date": date(2026, 2, 19),
        }
    )

    found = await repo.get_application_by_id(tenant.id, app_obj.id)
    not_found = await repo.get_application_by_id(another_tenant.id, app_obj.id)

    assert found is not None
    assert not_found is None


@pytest.mark.asyncio
async def test_list_applications_supports_filters_pagination_and_sorting(db_session):
    tenant = await _create_tenant(db_session, "ListTenant")
    another_tenant = await _create_tenant(db_session, "ListTenantOther")
    repo = ApplicationRepository(db_session)

    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role 1",
            "company": "Acme",
            "status": ApplicationStatus.applied,
            "location": "Remote",
            "applied_date": date(2026, 2, 1),
        }
    )
    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role 2",
            "company": "Acme Labs",
            "status": ApplicationStatus.screening,
            "location": "Remote",
            "applied_date": date(2026, 2, 2),
        }
    )
    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role 3",
            "company": "Globex",
            "status": ApplicationStatus.screening,
            "location": "Remote",
            "applied_date": date(2026, 2, 3),
        }
    )
    await repo.create_application(
        {
            "tenant_id": another_tenant.id,
            "title": "Other Tenant Role",
            "company": "Acme",
            "status": ApplicationStatus.screening,
            "location": "Onsite",
            "applied_date": date(2026, 2, 4),
        }
    )

    filtered = await repo.list_applications(
        tenant_id=tenant.id,
        limit=10,
        offset=0,
        status=ApplicationStatus.screening,
        company="acme",
        sort_by="applied_date",
        sort_order="asc",
    )

    assert len(filtered) == 1
    assert filtered[0].title == "Role 2"

    paged = await repo.list_applications(
        tenant_id=tenant.id,
        limit=1,
        offset=1,
        sort_by="applied_date",
        sort_order="asc",
    )
    assert len(paged) == 1
    assert paged[0].title == "Role 2"

    safe_sort = await repo.list_applications(
        tenant_id=tenant.id,
        limit=10,
        offset=0,
        sort_by="not_allowed",
        sort_order="asc",
    )
    assert len(safe_sort) == 3


@pytest.mark.asyncio
async def test_update_application_applies_updates_and_returns_none_when_missing(
    db_session,
):
    tenant = await _create_tenant(db_session, "UpdateTenant")
    another_tenant = await _create_tenant(db_session, "UpdateTenantOther")
    repo = ApplicationRepository(db_session)

    app_obj = await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Original Title",
            "company": "Original Co",
            "location": "Remote",
            "applied_date": date(2026, 2, 10),
        }
    )

    updated = await repo.update_application(
        tenant.id,
        app_obj.id,
        {
            "title": "Updated Title",
            "status": ApplicationStatus.interview,
        },
    )

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.status == ApplicationStatus.interview

    missing = await repo.update_application(
        another_tenant.id,
        app_obj.id,
        {"title": "Should Not Update"},
    )
    assert missing is None


@pytest.mark.asyncio
async def test_soft_delete_marks_record_and_hides_from_base_queries(db_session):
    tenant = await _create_tenant(db_session, "SoftDeleteTenant")
    repo = ApplicationRepository(db_session)

    app_obj = await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Delete Me",
            "company": "Delete Co",
            "location": "Remote",
            "applied_date": date(2026, 2, 11),
        }
    )

    deleted = await repo.soft_delete_application(tenant.id, app_obj.id)
    assert deleted is not None
    assert deleted.deleted_at is not None

    found_after_delete = await repo.get_application_by_id(tenant.id, app_obj.id)
    listed_after_delete = await repo.list_applications(
        tenant_id=tenant.id,
        limit=10,
        offset=0,
    )

    assert found_after_delete is None
    assert all(application.id != app_obj.id for application in listed_after_delete)


@pytest.mark.asyncio
async def test_get_dashboard_summary_returns_per_status_counts(db_session):
    tenant = await _create_tenant(db_session, "DashboardTenant")
    repo = ApplicationRepository(db_session)

    today = datetime.now(timezone.utc).date()

    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role A",
            "company": "Contoso",
            "status": ApplicationStatus.applied,
            "location": "Remote",
            "applied_date": today,
        }
    )
    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role B",
            "company": "Contoso",
            "status": ApplicationStatus.applied,
            "location": "Remote",
            "applied_date": today - timedelta(days=5),
        }
    )
    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role C",
            "company": "Contoso",
            "status": ApplicationStatus.offer,
            "location": "Remote",
            "applied_date": today - timedelta(days=10),
        }
    )
    await repo.create_application(
        {
            "tenant_id": tenant.id,
            "title": "Role D",
            "company": "Contoso",
            "status": ApplicationStatus.rejected,
            "location": "Remote",
            "applied_date": today - timedelta(days=40),
        }
    )

    summary = await repo.get_dashboard_summary(tenant.id)

    assert summary["applied"] == 2
    assert summary["offer"] == 1
    assert summary["screening"] == 0
    assert summary["applied_last_7_days"] == 2
    assert summary["applied_last_30_days"] == 3
