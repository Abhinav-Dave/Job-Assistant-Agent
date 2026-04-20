"""UserProfile, WorkHistoryItem, EducationItem, UpdateUserRequest (PRD Sections 10–12)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from re import fullmatch
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_YEAR_MONTH_PATTERN = r"\d{4}-(0[1-9]|1[0-2])"


def _is_year_month(value: str) -> bool:
    return bool(fullmatch(_YEAR_MONTH_PATTERN, value))


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
    start_date: str = Field(description='Month "YYYY-MM"')
    end_date: str | None = None
    is_current: bool = False
    bullets: list[str] = Field(default_factory=list)
    display_order: int = 0

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: str) -> str:
        if not _is_year_month(v):
            raise ValueError('start_date must be "YYYY-MM"')
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not _is_year_month(v):
            raise ValueError('end_date must be "YYYY-MM" or null')
        return v


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
