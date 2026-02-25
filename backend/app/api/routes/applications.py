from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_application_service, get_current_tenant
from app.models.application import ApplicationStatus
from app.models.tenant import Tenant
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListParams,
    ApplicationResponse,
    ApplicationUpdate,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post(
    "", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_application(
    payload: ApplicationCreate,
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_application_service),
) -> ApplicationResponse:
    return await service.create_application(tenant.id, payload)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application_by_id(
    application_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_application_service),
) -> ApplicationResponse:
    application = await service.get_application_by_id(tenant.id, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_application_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    company: str | None = Query(default=None),
    sort_by: Literal["applied_date", "created_at", "company", "status"] = Query(
        default="created_at"
    ),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
) -> list[ApplicationResponse]:
    params = ApplicationListParams(
        limit=limit,
        offset=offset,
        status=status_filter,
        company=company,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await service.list_applications(tenant.id, params)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_application_service),
) -> ApplicationResponse:
    updated = await service.update_application(tenant.id, application_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated


@router.delete("/{application_id}", response_model=ApplicationResponse)
async def soft_delete_application(
    application_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    service: Any = Depends(get_application_service),
) -> ApplicationResponse:
    deleted = await service.soft_delete_application(tenant.id, application_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return deleted
