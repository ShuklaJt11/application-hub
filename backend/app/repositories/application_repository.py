from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.application import Application, ApplicationStatus


class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self, tenant_id: UUID) -> Select[tuple[Application]]:
        return select(Application).where(
            Application.tenant_id == tenant_id,
            Application.deleted_at.is_(None),
        )

    async def create_application(self, data: dict) -> Application:
        application = Application(**data)
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def get_application_by_id(
        self, tenant_id: UUID, application_id: UUID
    ) -> Application | None:
        query = self._base_query(tenant_id).where(Application.id == application_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_applications(
        self,
        tenant_id: UUID,
        limit: int,
        offset: int,
        status: ApplicationStatus | None = None,
        company: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Application]:
        query = self._base_query(tenant_id)

        if status is not None:
            query = query.where(Application.status == status)

        if company is not None:
            query = query.where(Application.company.ilike(f"%{company.strip()}%"))

        allowed_sort_fields = {
            "applied_date": Application.applied_date,
            "created_at": Application.created_at,
            "company": Application.company,
            "status": Application.status,
        }
        sort_column = allowed_sort_fields.get(sort_by, Application.created_at)
        sort_direction = asc if sort_order.lower() == "asc" else desc
        query = query.order_by(sort_direction(sort_column))

        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_application(
        self, tenant_id: UUID, application_id: UUID, updates: dict
    ) -> Application | None:
        application = await self.get_application_by_id(tenant_id, application_id)
        if application is None:
            return None

        for field, value in updates.items():
            if hasattr(application, field):
                setattr(application, field, value)

        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def soft_delete_application(
        self, tenant_id: UUID, application_id: UUID
    ) -> Application | None:
        application = await self.get_application_by_id(tenant_id, application_id)
        if application is None:
            return None

        application.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def get_dashboard_summary(self, tenant_id: UUID) -> dict[str, int]:
        query = (
            select(Application.status, func.count(Application.id))
            .where(
                Application.tenant_id == tenant_id,
                Application.deleted_at.is_(None),
            )
            .group_by(Application.status)
        )

        result = await self.session.execute(query)
        summary = {
            "applied": 0,
            "screening": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
        }

        for status, count in result.all():
            summary[status.value] = int(count)

        today = datetime.now(timezone.utc).date()
        seven_days_ago = today - timedelta(days=6)
        thirty_days_ago = today - timedelta(days=29)

        last_7_days = await self.session.scalar(
            select(func.count(Application.id)).where(
                Application.tenant_id == tenant_id,
                Application.deleted_at.is_(None),
                Application.applied_date >= seven_days_ago,
                Application.applied_date <= today,
            )
        )
        last_30_days = await self.session.scalar(
            select(func.count(Application.id)).where(
                Application.tenant_id == tenant_id,
                Application.deleted_at.is_(None),
                Application.applied_date >= thirty_days_ago,
                Application.applied_date <= today,
            )
        )

        summary["applied_last_7_days"] = int(last_7_days or 0)
        summary["applied_last_30_days"] = int(last_30_days or 0)

        return summary
