import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.models.application import ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListParams,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService


class _FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def setex(self, key: str, _ttl: int, value: str) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0


@pytest.mark.asyncio
async def test_create_application_adds_tenant_id_and_calls_repository():
    repository = AsyncMock()
    repository.create_application = AsyncMock(return_value={"id": uuid.uuid4()})
    service = ApplicationService(repository=repository)

    tenant_id = uuid.uuid4()
    payload = ApplicationCreate(
        title="Backend Engineer",
        company="Contoso",
        location="Remote",
        applied_date=date(2026, 2, 24),
        status="screening",
    )

    await service.create_application(tenant_id, payload)

    repository.create_application.assert_awaited_once()
    data = repository.create_application.await_args.args[0]
    assert data["tenant_id"] == tenant_id
    assert data["status"] == ApplicationStatus.screening


@pytest.mark.asyncio
async def test_list_applications_passes_validated_params_to_repository():
    repository = AsyncMock()
    repository.list_applications = AsyncMock(return_value=[])
    service = ApplicationService(repository=repository)

    tenant_id = uuid.uuid4()
    params = ApplicationListParams(
        limit=10,
        offset=5,
        status="interview",
        company="Acme",
        sort_by="applied_date",
        sort_order="asc",
    )

    await service.list_applications(tenant_id, params)

    repository.list_applications.assert_awaited_once_with(
        tenant_id=tenant_id,
        limit=10,
        offset=5,
        status=ApplicationStatus.interview,
        company="Acme",
        sort_by="applied_date",
        sort_order="asc",
    )


@pytest.mark.asyncio
async def test_update_application_uses_dynamic_update_payload():
    repository = AsyncMock()
    repository.update_application = AsyncMock(return_value={"id": uuid.uuid4()})
    service = ApplicationService(repository=repository)

    tenant_id = uuid.uuid4()
    application_id = uuid.uuid4()
    payload = ApplicationUpdate(status="offer", notes="Strong fit")

    await service.update_application(tenant_id, application_id, payload)

    repository.update_application.assert_awaited_once_with(
        tenant_id,
        application_id,
        {"status": ApplicationStatus.offer, "notes": "Strong fit"},
    )


@pytest.mark.asyncio
async def test_get_dashboard_summary_uses_repository_then_caches_result():
    repository = AsyncMock()
    repository.get_dashboard_summary = AsyncMock(
        return_value={
            "applied": 2,
            "screening": 1,
            "interview": 0,
            "offer": 1,
            "rejected": 3,
            "applied_last_7_days": 4,
            "applied_last_30_days": 6,
        }
    )
    fake_redis = _FakeRedis()
    service = ApplicationService(repository=repository, redis_client=fake_redis)

    tenant_id = uuid.uuid4()

    first = await service.get_dashboard_summary(tenant_id)
    second = await service.get_dashboard_summary(tenant_id)

    assert first.total == 7
    assert second.total == 7
    assert second.by_status.rejected == 3
    assert second.trends.applied_last_7_days == 4
    assert second.trends.applied_last_30_days == 6
    repository.get_dashboard_summary.assert_awaited_once_with(tenant_id)


@pytest.mark.asyncio
async def test_create_update_delete_invalidate_dashboard_cache():
    repository = AsyncMock()
    repository.create_application = AsyncMock(return_value={"id": uuid.uuid4()})
    repository.update_application = AsyncMock(return_value={"id": uuid.uuid4()})
    repository.soft_delete_application = AsyncMock(return_value={"id": uuid.uuid4()})
    fake_redis = _FakeRedis()
    service = ApplicationService(repository=repository, redis_client=fake_redis)

    tenant_id = uuid.uuid4()
    cache_key = f"dashboard:{tenant_id}"
    fake_redis.store[cache_key] = "cached"

    payload = ApplicationCreate(
        title="Backend Engineer",
        company="Contoso",
        location="Remote",
        applied_date=date(2026, 2, 24),
        status="applied",
    )
    await service.create_application(tenant_id, payload)
    assert cache_key not in fake_redis.store

    fake_redis.store[cache_key] = "cached"
    await service.update_application(
        tenant_id,
        uuid.uuid4(),
        ApplicationUpdate(status="offer"),
    )
    assert cache_key not in fake_redis.store

    fake_redis.store[cache_key] = "cached"
    await service.soft_delete_application(tenant_id, uuid.uuid4())
    assert cache_key not in fake_redis.store
