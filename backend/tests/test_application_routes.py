import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_application_service, get_current_tenant
from app.api.routes.applications import router as applications_router


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
