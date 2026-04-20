"""ResumeScoreRequest, ResumeScoreResult (PRD Section 12)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ResumeScoreRequest(BaseModel):
    """Inputs for resume analysis (JSON / form fields; file upload handled at route)."""

    model_config = ConfigDict(extra="forbid")

    resume_text: str | None = None
    jd_text: str | None = None
    jd_url: str | None = None


class ResumeScoreResult(BaseModel):
    """`POST /api/resume/analyze` success payload."""

    model_config = ConfigDict(extra="forbid")

    match_score: int = Field(ge=0, le=100)
    grade: str = Field(min_length=1, max_length=4)
    summary: str
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    jd_key_requirements: list[str]
    ats_risk: Literal["low", "medium", "high"]
    ats_risk_reason: str
