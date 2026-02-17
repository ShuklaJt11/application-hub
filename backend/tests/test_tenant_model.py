import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.tenant import Tenant
from app.models.tenant_user import TenantRole, TenantUser
from app.models.user import User


@pytest.mark.asyncio
async def test_create_tenant_sets_defaults(db_session):
    tenant = Tenant(name="Acme")

    db_session.add(tenant)
    await db_session.flush()
    await db_session.refresh(tenant)

    assert tenant.id is not None
    assert tenant.created_at is not None


@pytest.mark.asyncio
async def test_tenant_name_cannot_be_null(db_session):
    db_session.add(Tenant(name=None))

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_persists_and_round_trips(db_session):
    tenant = Tenant(name="RoundTripTenant")

    db_session.add(tenant)
    await db_session.commit()

    stored = await db_session.scalar(
        select(Tenant).where(Tenant.name == "RoundTripTenant")
    )

    assert stored is not None
    assert stored.id is not None
    assert stored.created_at is not None


@pytest.mark.asyncio
async def test_tenant_user_links_relationship(db_session):
    user = User(
        email="tenant-link@example.com",
        username="tenant_link_user",
        first_name="Tenant",
        last_name="Link",
        hashed_password="hashed-tenant-link",
    )
    tenant = Tenant(name="LinkTenant")
    db_session.add_all([user, tenant])
    await db_session.flush()

    membership = TenantUser(
        user_id=user.id, tenant_id=tenant.id, role=TenantRole.member
    )
    db_session.add(membership)
    await db_session.flush()

    stored_tenant = await db_session.scalar(
        select(Tenant)
        .options(selectinload(Tenant.user_links))
        .where(Tenant.id == tenant.id)
    )

    assert stored_tenant is not None
    assert len(stored_tenant.user_links) == 1
    assert stored_tenant.user_links[0].user_id == user.id
    assert stored_tenant.user_links[0].role == TenantRole.member


@pytest.mark.asyncio
async def test_deleting_tenant_cascades_tenant_users(db_session):
    user = User(
        email="tenant-cascade@example.com",
        username="tenant_cascade_user",
        first_name="Tenant",
        last_name="Cascade",
        hashed_password="hashed-tenant-cascade",
    )
    tenant = Tenant(name="CascadeTenant")
    db_session.add_all([user, tenant])
    await db_session.flush()

    membership = TenantUser(user_id=user.id, tenant_id=tenant.id, role=TenantRole.admin)
    db_session.add(membership)
    await db_session.flush()

    await db_session.delete(tenant)
    await db_session.flush()

    remaining = await db_session.scalar(
        select(TenantUser).where(TenantUser.id == membership.id)
    )
    assert remaining is None
