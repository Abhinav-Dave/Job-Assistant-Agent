"""Application, CreateApplicationRequest, UpdateApplicationRequest (PRD Section 12)."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApplicationStatus(str, Enum):
    """`applications.status` CHECK constraint (PRD Section 10)."""

    saved = "saved"
    submitted = "submitted"
    response_received = "response_received"
    interview_requested = "interview_requested"
    interview_completed = "interview_completed"
    onsite_requested = "onsite_requested"
    offer_received = "offer_received"
    rejected = "rejected"
    withdrawn = "withdrawn"


class CreateApplicationRequest(BaseModel):
    """`POST /api/applications` body."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    company: str = Field(min_length=1)
    role: str = Field(min_length=1)
    jd_url: str | None = None
    jd_text: str | None = None
    status: ApplicationStatus = ApplicationStatus.saved
    notes: str | None = None
    date_applied: date | None = None


class UpdateApplicationRequest(BaseModel):
    """`PATCH /api/applications/{id}` body — any subset."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    company: str | None = Field(default=None, min_length=1)
    role: str | None = Field(default=None, min_length=1)
    jd_url: str | None = None
    jd_text: str | None = None
    status: ApplicationStatus | None = None
    notes: str | None = None
    date_applied: date | None = None
    last_score: int | None = Field(default=None, ge=0, le=100)


class Application(BaseModel):
    """Single application row + API resource."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    id: UUID
    user_id: UUID
    company: str
    role: str
    jd_url: str | None = None
    jd_text: str | None = None
    status: ApplicationStatus
    notes: str | None = None
    date_applied: date | None = None
    last_score: int | None = Field(default=None, ge=0, le=100)
    created_at: datetime
    updated_at: datetime


class ResumeScoreReport(BaseModel):
    """Persisted resume-vs-jd scoring report for an application."""

    model_config = ConfigDict(extra="forbid")

    application_id: UUID
    user_id: UUID
    match_score: int = Field(ge=0, le=100)
    grade: str
    summary: str
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    jd_key_requirements: list[str]
    ats_risk: str
    ats_risk_reason: str
    created_at: datetime
    updated_at: datetime


class UpsertResumeScoreReportRequest(BaseModel):
    """Upsert payload for persisted score reports."""

    model_config = ConfigDict(extra="forbid")

    match_score: int = Field(ge=0, le=100)
    grade: str
    summary: str
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    jd_key_requirements: list[str]
    ats_risk: str
    ats_risk_reason: str
