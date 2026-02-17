import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.tenant import Tenant
from app.models.tenant_user import TenantRole, TenantUser
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user_sets_defaults(db_session):
    user = User(
        email="alice@example.com",
        username="alice",
        first_name="Alice",
        last_name="Doe",
        hashed_password="hashed-secret",
    )

    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.is_active is True
    assert user.created_at is not None
    assert user.last_update is not None


@pytest.mark.asyncio
async def test_user_email_must_be_unique(db_session):
    first = User(
        email="dup@example.com",
        username="dup_1",
        first_name="First",
        last_name="User",
        hashed_password="hashed-1",
    )
    second = User(
        email="dup@example.com",
        username="dup_2",
        first_name="Second",
        last_name="User",
        hashed_password="hashed-2",
    )

    db_session.add(first)
    await db_session.flush()

    db_session.add(second)
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_username_must_be_unique(db_session):
    first = User(
        email="unique1@example.com",
        username="same_username",
        first_name="First",
        last_name="User",
        hashed_password="hashed-1",
    )
    second = User(
        email="unique2@example.com",
        username="same_username",
        first_name="Second",
        last_name="User",
        hashed_password="hashed-2",
    )

    db_session.add(first)
    await db_session.flush()

    db_session.add(second)
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing_field", ["first_name", "last_name", "hashed_password"]
)
async def test_user_required_fields_cannot_be_null(db_session, missing_field):
    payload = {
        "email": "required@example.com",
        "username": "required_user",
        "first_name": "Required",
        "last_name": "User",
        "hashed_password": "hashed-required",
    }
    payload[missing_field] = None

    db_session.add(User(**payload))
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_persists_and_round_trips(db_session):
    user = User(
        email="roundtrip@example.com",
        username="round_trip",
        first_name="Round",
        last_name="Trip",
        hashed_password="hashed-roundtrip",
    )
    db_session.add(user)
    await db_session.commit()

    stored = await db_session.scalar(
        select(User).where(User.email == "roundtrip@example.com")
    )

    assert stored is not None
    assert stored.username == "round_trip"
    assert stored.first_name == "Round"
    assert stored.last_name == "Trip"
    assert stored.is_active is True


@pytest.mark.asyncio
async def test_user_last_update_changes_on_update(db_session):
    user = User(
        email="update@example.com",
        username="update_user",
        first_name="Before",
        last_name="Update",
        hashed_password="hashed-update",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    initial_last_update = user.last_update

    user.first_name = "After"
    await db_session.flush()
    await db_session.refresh(user)

    assert user.last_update is not None
    assert user.last_update >= initial_last_update


@pytest.mark.asyncio
async def test_user_tenant_links_relationship(db_session):
    user = User(
        email="relation@example.com",
        username="relation_user",
        first_name="Rel",
        last_name="User",
        hashed_password="hashed-relation",
    )
    tenant = Tenant(name="Acme")
    db_session.add_all([user, tenant])
    await db_session.flush()

    membership = TenantUser(
        user_id=user.id, tenant_id=tenant.id, role=TenantRole.member
    )
    db_session.add(membership)
    await db_session.flush()
    stored_user = await db_session.scalar(
        select(User).options(selectinload(User.tenant_links)).where(User.id == user.id)
    )

    assert stored_user is not None
    assert len(stored_user.tenant_links) == 1
    assert stored_user.tenant_links[0].tenant_id == tenant.id
    assert stored_user.tenant_links[0].role == TenantRole.member


@pytest.mark.asyncio
async def test_deleting_user_cascades_tenant_users(db_session):
    user = User(
        email="cascade@example.com",
        username="cascade_user",
        first_name="Cascade",
        last_name="User",
        hashed_password="hashed-cascade",
    )
    tenant = Tenant(name="CascadeTenant")
    db_session.add_all([user, tenant])
    await db_session.flush()

    membership = TenantUser(user_id=user.id, tenant_id=tenant.id, role=TenantRole.admin)
    db_session.add(membership)
    await db_session.flush()

    await db_session.delete(user)
    await db_session.flush()

    remaining = await db_session.scalar(
        select(TenantUser).where(TenantUser.user_id == membership.user_id)
    )
    assert remaining is None

    await db_session.execute(delete(Tenant).where(Tenant.id == tenant.id))
    await db_session.flush()
