import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class TenantRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class TenantUser(Base):
    __tablename__ = "tenant_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[TenantRole] = mapped_column(
        Enum(TenantRole, name="tenant_role"),
        nullable=False,
        server_default=TenantRole.member.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="tenant_links")
    tenant: Mapped["Tenant"] = relationship(back_populates="user_links")

    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_tenant_users_user_tenant"),
        Index("ix_tenant_users_user_id", "user_id"),
        Index("ix_tenant_users_tenant_id", "tenant_id"),
    )
