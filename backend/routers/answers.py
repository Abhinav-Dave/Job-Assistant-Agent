"""POST /api/generate/answer (PRD Section 12)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from agents.answer_generator import AgentError as AnswerAgentError
from agents.answer_generator import generate_tailored_answer
from exceptions import JsonHttpError
from middleware.auth import get_current_user
from routers.mock_data import mock_user_profile
from schemas.answer import AnswerRequest, AnswerResult
from schemas.common import AgentError
from services.llm import LLMError
from tools.scraper import best_effort_jd_text

router = APIRouter(tags=["answers"])


@router.post("/generate/answer", response_model=AnswerResult)
async def generate_answer(
    body: AnswerRequest,
    user_id: str = Depends(get_current_user),
) -> AnswerResult:
    """Generate a tailored answer using the real answer agent (Gemini → Groq → fallback).

    Job context uses ``jd_url`` and/or ``jd_text`` (URL scrape first, then pasted text if needed).
    If ``profile`` is omitted, the same mock profile as ``GET /api/users/me`` is used; pass ``profile``
    in the JSON body to use your real resume data.
    """
    jd = best_effort_jd_text(
        body.jd_url.strip() if body.jd_url else None,
        body.jd_text.strip() if body.jd_text else None,
    )
    if not jd:
        raise JsonHttpError(
            422,
            AgentError(
                error="jd_scrape_failed",
                message=(
                    "Could not get enough job description text. "
                    "Paste the full posting into jd_text (required for many ATS pages)."
                ),
                detail=None,
            ).model_dump(),
        )

    if body.profile is not None:
        profile = body.profile.model_copy(update={"id": UUID(user_id)})
    else:
        profile = mock_user_profile(
            user_id=user_id,
            email="jane@example.com",
            full_name="Jane Smith",
            onboarding_complete=True,
        )

    try:
        return generate_tailored_answer(body.question.strip(), profile, jd)
    except AnswerAgentError as exc:
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
