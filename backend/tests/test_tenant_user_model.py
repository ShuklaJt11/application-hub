import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.tenant import Tenant
from app.models.tenant_user import TenantRole, TenantUser
from app.models.user import User


async def _create_user_and_tenant(db_session):
    user = User(
        email=f"tenant-user-{uuid.uuid4()}@example.com",
        username=f"tenant_user_{uuid.uuid4().hex[:8]}",
        first_name="Tenant",
        last_name="User",
        hashed_password="hashed-tenant-user",
    )
    tenant = Tenant(name=f"Tenant-{uuid.uuid4().hex[:8]}")
    db_session.add_all([user, tenant])
    await db_session.flush()
    return user, tenant


@pytest.mark.asyncio
async def test_create_tenant_user_sets_default_role_and_timestamp(db_session):
    user, tenant = await _create_user_and_tenant(db_session)

    membership = TenantUser(user_id=user.id, tenant_id=tenant.id)
    db_session.add(membership)
    await db_session.flush()
    await db_session.refresh(membership)

    assert membership.id is not None
    assert membership.created_at is not None
    assert membership.role == TenantRole.member


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [TenantRole.admin, TenantRole.member])
async def test_tenant_user_accepts_valid_roles(db_session, role):
    user, tenant = await _create_user_and_tenant(db_session)

    membership = TenantUser(user_id=user.id, tenant_id=tenant.id, role=role)
    db_session.add(membership)
    await db_session.flush()

    assert membership.role == role


@pytest.mark.asyncio
async def test_tenant_user_user_tenant_pair_must_be_unique(db_session):
    user, tenant = await _create_user_and_tenant(db_session)

    first = TenantUser(user_id=user.id, tenant_id=tenant.id, role=TenantRole.member)
    second = TenantUser(user_id=user.id, tenant_id=tenant.id, role=TenantRole.admin)

    db_session.add(first)
    await db_session.flush()

    db_session.add(second)
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_user_requires_existing_foreign_keys(db_session):
    membership = TenantUser(
        user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role=TenantRole.member
    )
    db_session.add(membership)

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_user_relationship_backrefs(db_session):
    user, tenant = await _create_user_and_tenant(db_session)
    membership = TenantUser(user_id=user.id, tenant_id=tenant.id, role=TenantRole.admin)
    db_session.add(membership)
    await db_session.flush()

    stored_membership = await db_session.scalar(
        select(TenantUser)
        .options(selectinload(TenantUser.user), selectinload(TenantUser.tenant))
        .where(TenantUser.id == membership.id)
    )

    assert stored_membership is not None
    assert stored_membership.user is not None
    assert stored_membership.tenant is not None
    assert stored_membership.user.id == user.id
    assert stored_membership.tenant.id == tenant.id
