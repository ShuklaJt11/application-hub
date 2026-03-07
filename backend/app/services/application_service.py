import os
from uuid import UUID

import redis.asyncio as redis

from app.models.application import Application
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDashboardResponse,
    ApplicationListParams,
    ApplicationStatusBreakdown,
    ApplicationTrendSummary,
    ApplicationUpdate,
)

DASHBOARD_CACHE_TTL_SECONDS = int(os.getenv("DASHBOARD_CACHE_TTL_SECONDS", "60"))


class ApplicationService:
    def __init__(
        self,
        repository: ApplicationRepository,
        redis_client: redis.Redis | None = None,
    ):
        self.repository = repository
        self.redis_client = redis_client

    @staticmethod
    def _dashboard_cache_key(tenant_id: UUID) -> str:
        return f"dashboard:{tenant_id}"

    async def _invalidate_dashboard_cache(self, tenant_id: UUID) -> None:
        if self.redis_client is None:
            return

        await self.redis_client.delete(self._dashboard_cache_key(tenant_id))

    async def create_application(
        self, tenant_id: UUID, payload: ApplicationCreate
    ) -> Application:
        data = payload.model_dump(exclude_none=True)
        data["tenant_id"] = tenant_id
        application = await self.repository.create_application(data)
        await self._invalidate_dashboard_cache(tenant_id)
        return application

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

    async def get_dashboard_summary(
        self, tenant_id: UUID
    ) -> ApplicationDashboardResponse:
        cache_key = self._dashboard_cache_key(tenant_id)
        if self.redis_client is not None:
            cached_payload = await self.redis_client.get(cache_key)
            if cached_payload is not None:
                return ApplicationDashboardResponse.model_validate_json(cached_payload)

        raw_summary = await self.repository.get_dashboard_summary(tenant_id)
        breakdown = ApplicationStatusBreakdown(
            applied=raw_summary["applied"],
            screening=raw_summary["screening"],
            interview=raw_summary["interview"],
            offer=raw_summary["offer"],
            rejected=raw_summary["rejected"],
        )
        trends = ApplicationTrendSummary(
            applied_last_7_days=raw_summary["applied_last_7_days"],
            applied_last_30_days=raw_summary["applied_last_30_days"],
        )
        dashboard = ApplicationDashboardResponse(
            total=(
                breakdown.applied
                + breakdown.screening
                + breakdown.interview
                + breakdown.offer
                + breakdown.rejected
            ),
            by_status=breakdown,
            trends=trends,
        )

        if self.redis_client is not None:
            await self.redis_client.setex(
                cache_key,
                DASHBOARD_CACHE_TTL_SECONDS,
                dashboard.model_dump_json(),
            )

        return dashboard

    async def update_application(
        self,
        tenant_id: UUID,
        application_id: UUID,
        payload: ApplicationUpdate,
    ) -> Application | None:
        updates = payload.model_dump(exclude_unset=True)
        updated = await self.repository.update_application(
            tenant_id, application_id, updates
        )
        if updated is not None:
            await self._invalidate_dashboard_cache(tenant_id)
        return updated

    async def soft_delete_application(
        self, tenant_id: UUID, application_id: UUID
    ) -> Application | None:
        deleted = await self.repository.soft_delete_application(
            tenant_id, application_id
        )
        if deleted is not None:
            await self._invalidate_dashboard_cache(tenant_id)
        return deleted
