from datetime import date

import pytest
from pydantic import ValidationError

from app.models.application import ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListParams,
    ApplicationUpdate,
)


def test_application_create_parses_status_enum_and_forbids_extra_fields():
    obj = ApplicationCreate(
        title="Software Engineer",
        company="Contoso",
        location="Remote",
        applied_date=date(2026, 2, 24),
        status="screening",
    )

    assert obj.status == ApplicationStatus.screening

    with pytest.raises(ValidationError):
        ApplicationCreate(
            title="Software Engineer",
            company="Contoso",
            location="Remote",
            applied_date=date(2026, 2, 24),
            unknown_field="x",
        )


def test_application_update_requires_at_least_one_field():
    with pytest.raises(ValidationError):
        ApplicationUpdate()


@pytest.mark.parametrize(
    "sort_by,sort_order",
    [
        ("applied_date", "asc"),
        ("created_at", "desc"),
        ("company", "asc"),
        ("status", "desc"),
    ],
)
def test_application_list_params_accept_only_whitelisted_sort(sort_by, sort_order):
    params = ApplicationListParams(sort_by=sort_by, sort_order=sort_order)

    assert params.sort_by == sort_by
    assert params.sort_order == sort_order


@pytest.mark.parametrize(
    "payload",
    [
        {"sort_by": "title"},
        {"sort_order": "up"},
        {"limit": 0},
        {"offset": -1},
    ],
)
def test_application_list_params_reject_invalid_values(payload):
    with pytest.raises(ValidationError):
        ApplicationListParams(**payload)
