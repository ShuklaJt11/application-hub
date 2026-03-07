import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_application_service, get_current_tenant
from app.api.routes.applications import router as applications_router
from app.services.application_service import ApplicationService


def _build_test_client(fake_service, tenant_id: uuid.UUID):
    app = FastAPI()
    app.include_router(applications_router)
    app.dependency_overrides[get_application_service] = lambda: fake_service
    app.dependency_overrides[get_current_tenant] = lambda: type(
        "TenantObj", (), {"id": tenant_id}
    )()
    return TestClient(app)


def _application_response(application_id: uuid.UUID, tenant_id: uuid.UUID) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": str(application_id),
        "tenant_id": str(tenant_id),
        "title": "Backend Engineer",
        "company": "Contoso",
        "status": "applied",
        "location": "Remote",
        "description": None,
        "salary_range": None,
        "notes": None,
        "url": None,
        "applied_date": str(date(2026, 2, 24)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "deleted_at": None,
    }


def test_create_application_route_calls_service_and_returns_payload():
    fake_service = AsyncMock()
    tenant_id = uuid.uuid4()
    application_id = uuid.uuid4()
    fake_service.create_application.return_value = _application_response(
        application_id, tenant_id
    )

    client = _build_test_client(fake_service, tenant_id)

    response = client.post(
        "/applications",
        json={
            "title": "Backend Engineer",
            "company": "Contoso",
            "location": "Remote",
            "applied_date": "2026-02-24",
            "status": "applied",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(application_id)
    fake_service.create_application.assert_awaited_once()


def test_get_application_by_id_returns_404_when_service_returns_none():
    fake_service = AsyncMock()
    tenant_id = uuid.uuid4()
    fake_service.get_application_by_id.return_value = None
    client = _build_test_client(fake_service, tenant_id)

    response = client.get(f"/applications/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_dashboard_summary_route_returns_cached_stats_payload():
    fake_service = AsyncMock()
    tenant_id = uuid.uuid4()
    fake_service.get_dashboard_summary.return_value = {
        "total": 5,
        "by_status": {
            "applied": 2,
            "screening": 1,
            "interview": 1,
            "offer": 1,
            "rejected": 0,
        },
        "trends": {
            "applied_last_7_days": 3,
            "applied_last_30_days": 5,
        },
    }
    client = _build_test_client(fake_service, tenant_id)

    response = client.get("/applications/dashboard")

    assert response.status_code == 200
    assert response.json()["total"] == 5
    assert response.json()["by_status"]["applied"] == 2
    assert response.json()["trends"]["applied_last_7_days"] == 3
    fake_service.get_dashboard_summary.assert_awaited_once_with(tenant_id)


class _FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def setex(self, key: str, _ttl: int, value: str) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0


def test_create_application_route_invalidates_dashboard_cache_with_real_service():
    tenant_id = uuid.uuid4()
    application_id = uuid.uuid4()
    fake_repository = AsyncMock()
    fake_repository.create_application.return_value = _application_response(
        application_id, tenant_id
    )
    fake_redis = _FakeRedis()
    cache_key = f"dashboard:{tenant_id}"
    fake_redis.store[cache_key] = "cached"

    service = ApplicationService(repository=fake_repository, redis_client=fake_redis)
    client = _build_test_client(service, tenant_id)

    response = client.post(
        "/applications",
        json={
            "title": "Backend Engineer",
            "company": "Contoso",
            "location": "Remote",
            "applied_date": "2026-02-24",
            "status": "applied",
        },
    )

    assert response.status_code == 201
    assert cache_key not in fake_redis.store
