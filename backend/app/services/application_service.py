from uuid import UUID

from app.models.application import Application
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListParams,
    ApplicationUpdate,
)


class ApplicationService:
    def __init__(self, repository: ApplicationRepository):
        self.repository = repository

    async def create_application(
        self, tenant_id: UUID, payload: ApplicationCreate
    ) -> Application:
        data = payload.model_dump(exclude_none=True)
        data["tenant_id"] = tenant_id
        return await self.repository.create_application(data)

    async def get_application_by_id(
        self, tenant_id: UUID, application_id: UUID
    ) -> Application | None:
        return await self.repository.get_application_by_id(tenant_id, application_id)

    async def list_applications(
        self, tenant_id: UUID, params: ApplicationListParams
    ) -> list[Application]:
        return await self.repository.list_applications(
            tenant_id=tenant_id,
            limit=params.limit,
            offset=params.offset,
            status=params.status,
            company=params.company,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )

    async def update_application(
        self,
        tenant_id: UUID,
        application_id: UUID,
        payload: ApplicationUpdate,
    ) -> Application | None:
        updates = payload.model_dump(exclude_unset=True)
        return await self.repository.update_application(
            tenant_id, application_id, updates
        )

    async def soft_delete_application(
        self, tenant_id: UUID, application_id: UUID
    ) -> Application | None:
        return await self.repository.soft_delete_application(tenant_id, application_id)
