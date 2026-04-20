"""POST /api/resume/analyze (PRD Section 12)."""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from exceptions import JsonHttpError
from middleware.auth import get_current_user
from schemas.common import AgentError
from schemas.resume import ResumeScoreResult

router = APIRouter(tags=["resume"])


@router.post("/analyze", response_model=ResumeScoreResult)
async def analyze_resume(
    user_id: str = Depends(get_current_user),
    resume_file: UploadFile | None = File(None),
    resume_text: str | None = Form(None),
    jd_text: str | None = Form(None),
    jd_url: str | None = Form(None),
) -> ResumeScoreResult:
    """Resume scorer — Phase 4 mock (no agent)."""
    has_resume = resume_file is not None and bool(resume_file.filename)
    has_text = bool(resume_text and resume_text.strip())
    if not has_resume and not has_text:
        err = AgentError(
            error="invalid_input",
            message="Must provide either resume_file or resume_text",
            detail=None,
        )
        raise JsonHttpError(422, err.model_dump())

    has_jd = bool((jd_text and jd_text.strip()) or (jd_url and jd_url.strip()))
    if not has_jd:
        err = AgentError(
            error="invalid_input",
            message="Must provide jd_text and/or jd_url",
            detail=None,
        )
        raise JsonHttpError(422, err.model_dump())

    _ = user_id
    return ResumeScoreResult(
        match_score=74,
        grade="B",
        summary=(
            "Strong technical match, but missing infrastructure/deployment keywords "
            "that appear 4+ times in the JD."
        ),
        matched_skills=["Python", "REST APIs", "SQL", "React"],
        missing_skills=["Kubernetes", "Terraform", "CI/CD"],
        suggestions=[
            "Add any CI/CD experience (GitHub Actions, Jenkins) to your most recent role",
            "Mention cloud platform explicitly — the JD references AWS 4 times",
            (
                "Quantify achievements: 'built APIs' → "
                "'built 12 REST endpoints serving 50K req/day'"
            ),
        ],
        jd_key_requirements=[
            "Python",
            "Kubernetes",
            "SQL",
            "REST APIs",
            "CI/CD",
            "AWS",
        ],
        ats_risk="medium",
        ats_risk_reason=(
            "Missing 3 of 6 high-frequency JD keywords. "
            "ATS may filter before human review."
        ),
    )
