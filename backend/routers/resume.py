"""POST /api/resume/analyze (PRD Section 12)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from agents.resume_scorer import AgentError as ResumeAgentError
from agents.resume_scorer import analyze_resume_and_jd
from exceptions import JsonHttpError
from middleware.auth import get_current_user
from schemas.common import AgentError
from schemas.resume import ResumeScoreResult
from services.llm import LLMError
from tools.scraper import best_effort_jd_text

router = APIRouter(tags=["resume"])


def _resume_source_from_upload(content: bytes, filename: str | None) -> dict[str, str | bytes]:
    """Treat uploads as PDF when extension or magic bytes match; else UTF-8 / Latin-1 text (e.g. .md, .txt)."""
    if not content:
        raise JsonHttpError(
            422,
            AgentError(
                error="invalid_input",
                message="Resume file is empty.",
                detail=None,
            ).model_dump(),
        )
    name = (filename or "").lower()
    if name.endswith(".pdf") or content[:4] == b"%PDF":
        return {"type": "pdf", "data": content}
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return {"type": "text", "data": content.decode(encoding)}
        except UnicodeDecodeError:
            continue
    return {"type": "text", "data": content.decode("latin-1", errors="replace")}


@router.post("/analyze", response_model=ResumeScoreResult)
async def analyze_resume(
    user_id: str = Depends(get_current_user),
    resume_file: UploadFile | None = File(None),
    resume_text: str | None = Form(None),
    jd_text: str | None = Form(None),
    jd_url: str | None = Form(None),
) -> ResumeScoreResult:
    """Analyze resume (PDF or plain text / Markdown file or pasted text) against a job description.

    Provide ``jd_url``, ``jd_text``, or both: the server scrapes the URL first; if the page is too sparse
    (common on Workday / heavy JS ATS), pasted ``jd_text`` is used automatically when present.
    """
    has_resume_file = resume_file is not None and bool(resume_file.filename)
    has_resume_text = bool(resume_text and resume_text.strip())
    if not has_resume_file and not has_resume_text:
        err = AgentError(
            error="invalid_input",
            message="Must provide either resume_file or resume_text",
            detail=None,
        )
        raise JsonHttpError(422, err.model_dump())

    jd_url_stripped = jd_url.strip() if jd_url else ""
    jd_text_stripped = jd_text.strip() if jd_text else ""
    has_jd = bool(jd_text_stripped or jd_url_stripped)
    if not has_jd:
        err = AgentError(
            error="invalid_input",
            message="Must provide jd_text and/or jd_url",
            detail=None,
        )
        raise JsonHttpError(422, err.model_dump())

    if has_resume_file:
        assert resume_file is not None
        raw = await resume_file.read()
        resume_source = _resume_source_from_upload(raw, resume_file.filename)
    else:
        assert resume_text is not None
        resume_source = {"type": "text", "data": resume_text.strip()}

    merged_jd = best_effort_jd_text(
        jd_url_stripped or None,
        jd_text_stripped or None,
    )
    if not merged_jd:
        raise JsonHttpError(
            422,
            AgentError(
                error="jd_scrape_failed",
                message=(
                    "Could not get enough job description text from the URL or form. "
                    "Paste the full posting into jd_text (many ATS pages block simple scrapers)."
                ),
                detail=None,
            ).model_dump(),
        )
    jd_source = {"type": "text", "data": merged_jd}

    try:
        return analyze_resume_and_jd(resume_source, jd_source, user_id)
    except ResumeAgentError as exc:
        raise JsonHttpError(
            422,
            {
                "error": exc.error,
                "message": exc.message,
                "detail": exc.detail,
            },
        ) from exc
    except LLMError as exc:
        raise JsonHttpError(
            503,
            AgentError(
                error=exc.code,
                message=str(exc),
                detail=None,
            ).model_dump(),
        ) from exc
