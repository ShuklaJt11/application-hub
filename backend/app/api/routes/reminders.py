from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import get_current_tenant, get_reminder_service, rate_limit
from app.models.tenant import Tenant
from app.schemas.reminder import (
    ReminderCreate,
    ReminderProcessResponse,
    ReminderResponse,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(times=30, seconds=60)],
)
async def create_reminder(
    payload: ReminderCreate,
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_reminder_service),
) -> ReminderResponse:
    data = payload.model_dump(exclude_none=True)
    data["tenant_id"] = tenant.id
    return await service.create_reminder(data)


@router.post(
    "/process-due",
    response_model=ReminderProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[rate_limit(times=10, seconds=60)],
)
async def process_due_reminders(
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_reminder_service),
) -> ReminderProcessResponse:
    background_tasks.add_task(service.run_due_reminders_worker, tenant.id)
    return ReminderProcessResponse(message="Reminder processing started")
