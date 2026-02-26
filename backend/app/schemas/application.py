from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from app.models.application import ApplicationStatus
from app.schemas.clean_input_model import CleanInputModel


class ApplicationCreate(CleanInputModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    description: str | None = None
    salary_range: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    url: str | None = Field(default=None, max_length=500)
    applied_date: date
    status: ApplicationStatus | None = None


class ApplicationUpdate(CleanInputModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    salary_range: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    url: str | None = Field(default=None, max_length=500)
    applied_date: date | None = None
    status: ApplicationStatus | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "ApplicationUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self


class ApplicationListParams(CleanInputModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    status: ApplicationStatus | None = None
    company: str | None = Field(default=None, min_length=1, max_length=200)
    sort_by: Literal["applied_date", "created_at", "company", "status"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class ApplicationResponse(CleanInputModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    company: str
    status: ApplicationStatus
    location: str
    description: str | None
    salary_range: str | None
    notes: str | None
    url: str | None
    applied_date: date
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
