from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.tenant import Tenant  # noqa: E402,F401
from app.models.tenant_user import TenantUser  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
