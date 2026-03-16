from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.clean_input_model import CleanInputModel


class ReminderCreate(CleanInputModel):
    application_id: UUID
    remind_at: datetime
    message: str | None = Field(default=None, max_length=2000)


class ReminderResponse(CleanInputModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    remind_at: datetime
    message: str | None
    sent: bool
    created_at: datetime


class ReminderProcessResponse(CleanInputModel):
    message: str
