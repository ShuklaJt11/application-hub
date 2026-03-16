import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter

from app.api.deps import get_current_tenant, get_reminder_service
from app.api.routes.reminders import router as reminders_router


def _build_test_client(fake_service, tenant_id: uuid.UUID):
    FastAPILimiter.redis = None
    app = FastAPI()
    app.include_router(reminders_router)
    app.dependency_overrides[get_reminder_service] = lambda: fake_service
    app.dependency_overrides[get_current_tenant] = lambda: type(
        "TenantObj", (), {"id": tenant_id}
    )()
    return TestClient(app)


def test_create_reminder_route_calls_service_and_returns_payload():
    fake_service = AsyncMock()
    tenant_id = uuid.uuid4()
    reminder_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    application_id = uuid.uuid4()

    fake_service.create_reminder.return_value = {
        "id": str(reminder_id),
        "tenant_id": str(tenant_id),
        "application_id": str(application_id),
        "remind_at": now.isoformat(),
        "message": "Follow up",
        "sent": False,
        "created_at": now.isoformat(),
    }

    client = _build_test_client(fake_service, tenant_id)

    response = client.post(
        "/reminders",
        json={
            "application_id": str(application_id),
            "remind_at": now.isoformat(),
            "message": "Follow up",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(reminder_id)
    fake_service.create_reminder.assert_awaited_once()
    data = fake_service.create_reminder.await_args.args[0]
    assert data["tenant_id"] == tenant_id


def test_process_due_reminders_route_triggers_background_worker():
    fake_service = AsyncMock()
    tenant_id = uuid.uuid4()
    fake_service.run_due_reminders_worker.return_value = 0

    client = _build_test_client(fake_service, tenant_id)

    response = client.post("/reminders/process-due")

    assert response.status_code == 202
    assert response.json()["message"] == "Reminder processing started"
    fake_service.run_due_reminders_worker.assert_awaited_once_with(tenant_id)
