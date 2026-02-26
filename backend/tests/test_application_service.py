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
