"""UserProfile, WorkHistoryItem, EducationItem, UpdateUserRequest (PRD Sections 10–12)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

def _coerce_year_month(value: object, *, field_label: str) -> str:
    """Accept YYYY-MM, ISO dates (YYYY-MM-DD), and single-digit months; reject OpenAPI 'string' placeholders."""
    if value is None:
        raise ValueError(f"{field_label} is required")
    v = str(value).strip()
    low = v.lower()
    if low in ("string", "str"):
        raise ValueError(
            f'{field_label} must be YYYY-MM (e.g. 2022-06). '
            'Swagger UI often prefills the word "string" — replace it with a real date.'
        )
    if low in ("null", "none", ""):
        raise ValueError(f"{field_label} cannot be empty; use null only for end_date when current role")
    if "T" in v:
        v = v.split("T", 1)[0].strip()
    parts = v.split("-")
    if len(parts) >= 2 and parts[0].isdigit() and len(parts[0]) == 4 and parts[1].isdigit():
        y, m = int(parts[0]), int(parts[1])
        if 1000 <= y <= 9999 and 1 <= m <= 12:
            return f"{y:04d}-{m:02d}"
    raise ValueError(f'{field_label} must be "YYYY-MM" (received {value!r})')


def _coerce_end_date(value: object) -> str | None:
    if value is None:
        return None
    v = str(value).strip()
    low = v.lower()
    if low in ("", "null", "none", "string", "str"):
        return None
    return _coerce_year_month(v, field_label="end_date")


class UserPreferences(BaseModel):
    """Shape stored in `users.preferences` JSONB (PRD Section 10)."""

    model_config = ConfigDict(extra="forbid")

    desired_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    remote_preference: Literal["remote", "hybrid", "onsite"] | None = None
    salary_min: int | None = Field(default=None, ge=0)


class WorkHistoryItem(BaseModel):
    """Row shape for `work_history` and nested profile payload."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    company: str = Field(min_length=1)
    role: str = Field(min_length=1)
    start_date: str = Field(
        description='Month "YYYY-MM" (or YYYY-MM-DD; Swagger: do not leave the default "string").',
        examples=["2022-06"],
    )
    end_date: str | None = Field(
        default=None,
        description='Month "YYYY-MM", or null / omit for current role.',
        examples=["2023-12"],
    )
    is_current: bool = False
    bullets: list[str] = Field(default_factory=list)
    display_order: int = 0

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start_date(cls, v: object) -> str:
        return _coerce_year_month(v, field_label="start_date")

    @field_validator("end_date", mode="before")
    @classmethod
    def validate_end_date(cls, v: object) -> str | None:
        return _coerce_end_date(v)


class EducationItem(BaseModel):
    """Row shape for `education` and nested profile payload."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    institution: str = Field(min_length=1)
    degree: str = Field(min_length=1)
    field_of_study: str | None = None
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    gpa: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("9.99"))
    display_order: int = 0


class CreateUserRequest(BaseModel):
    """`POST /api/users` body — id must match JWT `sub` (PRD Section 12)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: EmailStr
    full_name: str = Field(min_length=1)


class UserProfile(BaseModel):
    """`GET /api/users/me` response (PRD Section 12)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: EmailStr
    full_name: str = Field(min_length=1)
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    skills: list[str] = Field(default_factory=list)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    work_history: list[WorkHistoryItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    onboarding_complete: bool = False
    created_at: datetime
    updated_at: datetime


class UpdateUserRequest(BaseModel):
    """`PATCH /api/users/me` — any subset of profile fields (PRD Section 12)."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    skills: list[str] | None = None
    preferences: UserPreferences | None = None
    work_history: list[WorkHistoryItem] | None = None
    education: list[EducationItem] | None = None
    onboarding_complete: bool | None = None
