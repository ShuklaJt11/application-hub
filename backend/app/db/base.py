from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import (  # type: ignore[attr-defined] # noqa: E402,F401
    Tenant,
    TenantUser,
    User,
)
