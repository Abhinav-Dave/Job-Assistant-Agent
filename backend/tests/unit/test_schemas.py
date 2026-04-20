"""Pydantic schema validation (PRD Section 19, Phase 3)."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from schemas.answer import AnswerRequest, AnswerResult
from schemas.application import (
    Application,
    ApplicationStatus,
    CreateApplicationRequest,
    UpdateApplicationRequest,
)
from schemas.autofill import AutofillResult, FieldMapping, FormField
from schemas.common import AgentError, HealthCheckResult
from schemas.resume import ResumeScoreRequest, ResumeScoreResult
from schemas.user import EducationItem, UpdateUserRequest, UserPreferences, UserProfile, WorkHistoryItem


def test_work_history_item_valid_and_invalid() -> None:
    wid = UUID("550e8400-e29b-41d4-a716-446655440001")
    valid = WorkHistoryItem(
        id=wid,
        company="Acme Corp",
        role="Engineer",
        start_date="2022-06",
        end_date=None,
        is_current=True,
        bullets=["Did things"],
        display_order=0,
    )
    assert valid.is_current is True

    with pytest.raises(ValidationError):
        WorkHistoryItem(
            id=wid,
            company="Acme",
            role="Eng",
            start_date="2022-13",
            end_date=None,
        )

    with pytest.raises(ValidationError):
        WorkHistoryItem(
            id=wid,
            company="Acme",
            role="Eng",
            start_date="2022-06",
            end_date="not-a-date",
        )


def test_education_item_gpa_bounds() -> None:
    eid = UUID("550e8400-e29b-41d4-a716-446655440002")
    row = EducationItem(
        id=eid,
        institution="University",
        degree="BSc",
        field_of_study="CS",
        graduation_year=2022,
        gpa=Decimal("3.80"),
        display_order=0,
    )
    assert row.gpa == Decimal("3.80")

    with pytest.raises(ValidationError):
        EducationItem(
            id=eid,
            institution="U",
            degree="BSc",
            gpa=Decimal("15.0"),
        )


def test_user_profile_and_update_roundtrip() -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440000")
    wh_id = UUID("550e8400-e29b-41d4-a716-446655440001")
    ed_id = UUID("550e8400-e29b-41d4-a716-446655440002")
    ts = datetime(2026, 4, 1, 10, 0, 0, tzinfo=timezone.utc)
    profile = UserProfile(
        id=uid,
        email="jane@example.com",
        full_name="Jane Smith",
        phone="416-555-0100",
        location="Toronto, ON",
        linkedin_url="https://linkedin.com/in/janesmith",
        portfolio_url="https://github.com/janesmith",
        skills=["Python", "FastAPI"],
        preferences=UserPreferences(
            desired_roles=["Backend Engineer"],
            remote_preference="hybrid",
            salary_min=85000,
        ),
        work_history=[
            WorkHistoryItem(
                id=wh_id,
                company="Acme Corp",
                role="Software Engineer",
                start_date="2022-06",
                end_date=None,
                is_current=True,
                bullets=["Built APIs"],
                display_order=0,
            )
        ],
        education=[
            EducationItem(
                id=ed_id,
                institution="University of Toronto",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                graduation_year=2022,
                gpa=Decimal("3.8"),
                display_order=0,
            )
        ],
        onboarding_complete=True,
        created_at=ts,
        updated_at=ts,
    )
    assert profile.email == "jane@example.com"

    partial = UpdateUserRequest(full_name="J. Smith", onboarding_complete=False)
    assert partial.full_name == "J. Smith"
    assert partial.onboarding_complete is False

    with pytest.raises(ValidationError):
        UpdateUserRequest(email="not-an-email")


def test_resume_score_result_invalid_score() -> None:
    with pytest.raises(ValidationError):
        ResumeScoreResult(
            match_score=101,
            grade="B",
            summary="x",
            matched_skills=[],
            missing_skills=[],
            suggestions=[],
            jd_key_requirements=[],
            ats_risk="medium",
            ats_risk_reason="reason",
        )

    ok = ResumeScoreResult(
        match_score=74,
        grade="B",
        summary="Strong match",
        matched_skills=["Python"],
        missing_skills=["K8s"],
        suggestions=["Add CI/CD"],
        jd_key_requirements=["Python", "SQL"],
        ats_risk="medium",
        ats_risk_reason="Missing keywords",
    )
    assert ok.match_score == 74

    ResumeScoreRequest(resume_text=None, jd_text="JD", jd_url=None)


def test_answer_request_requires_jd_source() -> None:
    AnswerRequest(question="Why you?", jd_text="Long jd...", jd_url=None)

    AnswerRequest(question="Why you?", jd_text=None, jd_url="https://example.com/job")

    with pytest.raises(ValidationError):
        AnswerRequest(question="Why?", jd_text=None, jd_url=None)

    with pytest.raises(ValidationError):
        AnswerRequest(question="", jd_text="jd")

    result = AnswerResult(answer="Text", word_count=100, question="Why?")
    assert result.word_count == 100

    with pytest.raises(ValidationError):
        AnswerResult(answer="x", word_count=-1, question="q")


def test_application_models() -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440000")
    aid = UUID("660e8400-e29b-41d4-a716-446655440000")
    ts = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)

    created = CreateApplicationRequest(
        company="Stripe",
        role="Backend Engineer",
        jd_url="https://stripe.com/jobs/123",
        status=ApplicationStatus.submitted,
        notes="Applied via LinkedIn",
        date_applied=date(2026, 4, 19),
    )
    assert created.status == ApplicationStatus.submitted

    app = Application(
        id=aid,
        user_id=uid,
        company="Stripe",
        role="Backend Engineer",
        jd_url="https://stripe.com/jobs/123",
        status=ApplicationStatus.submitted,
        date_applied=date(2026, 4, 19),
        last_score=80,
        created_at=ts,
        updated_at=ts,
    )
    assert app.last_score == 80

    upd = UpdateApplicationRequest(status=ApplicationStatus.interview_requested)
    assert upd.status == ApplicationStatus.interview_requested

    with pytest.raises(ValidationError):
        UpdateApplicationRequest(last_score=101)


def test_autofill_and_form_field() -> None:
    FormField(
        field_id="FirstName",
        name="first_name",
        label="First Name",
        field_type="text",
        placeholder="Jane",
    )

    mapping = FieldMapping(
        field_id="FirstName",
        field_label="First Name",
        field_type="text",
        profile_key="full_name",
        suggested_value="Jane",
        confidence=0.97,
    )

    result = AutofillResult(
        fill_rate=0.82,
        total_fields=17,
        mapped_fields=14,
        mappings=[mapping],
        unfilled_fields=["cover_letter"],
    )
    assert result.fill_rate == 0.82

    with pytest.raises(ValidationError):
        AutofillResult(
            fill_rate=0.5,
            total_fields=10,
            mapped_fields=11,
            mappings=[mapping],
            unfilled_fields=[],
        )

    with pytest.raises(ValidationError):
        FieldMapping(
            field_id="x",
            field_label="l",
            field_type="t",
            profile_key="p",
            suggested_value="v",
            confidence=1.5,
        )


def test_common_agent_error_and_health() -> None:
    err = AgentError(error="invalid_input", message="Bad", detail=None)
    assert err.detail is None

    with pytest.raises(ValidationError):
        AgentError(error="x", message="y", extra_field=1)  # type: ignore[call-arg]

    ts = datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc)
    health = HealthCheckResult(
        status="ok",
        database="connected",
        llm="reachable",
        version="1.0.0",
        timestamp=ts,
    )
    assert health.database == "connected"

    with pytest.raises(ValidationError):
        HealthCheckResult(
            status="degraded",
            database="connected",
            llm="reachable",
            version="1.0.0",
            timestamp=ts,
        )
