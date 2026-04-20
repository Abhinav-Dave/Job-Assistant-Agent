"""Resume scorer agent flow (PRD Section 7, Section 12)."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import ValidationError

from schemas.resume import ResumeScoreResult
from services.llm import LLMError, call_gemini, call_groq, load_prompt, parse_json_from_response
from tools.pdf_parser import extract_text_from_pdf
from tools.scraper import scrape_job_description

logger = logging.getLogger(__name__)

_MIN_TEXT_LENGTH = 100
_MAX_RESUME_CHARS = 6000
_MAX_JD_CHARS = 4000
_MAX_TOKENS = 1500
_RESUME_LLM_TIMEOUT = 45
_GEMINI_FAILOVER_CODES = frozenset({"llm_unavailable", "llm_empty_response"})

ResumeSourceType = Literal["pdf", "text"]
JDSourceType = Literal["url", "text"]


class AgentError(Exception):
    """Structured agent exception for predictable failures."""

    def __init__(self, error: str, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict[str, str | None]:
        return {"error": self.error, "message": self.message, "detail": self.detail}


def _normalize_source(data: Any) -> dict[str, Any]:
    if isinstance(data, Mapping):
        return {"type": data.get("type"), "data": data.get("data")}
    return {"type": getattr(data, "type", None), "data": getattr(data, "data", None)}


def _resolve_resume_text(resume_source: dict[str, Any]) -> str:
    source_type = resume_source.get("type")
    source_data = resume_source.get("data")

    if source_type == "pdf":
        if not isinstance(source_data, (bytes, bytearray)):
            raise AgentError("invalid_input", "resume_source.data must be PDF bytes when type=pdf")
        extracted = extract_text_from_pdf(bytes(source_data)).strip()
        if len(extracted) < _MIN_TEXT_LENGTH:
            raise AgentError(
                "pdf_no_text",
                "PDF appears to be a scanned image. Please paste text instead.",
            )
        return extracted

    if source_type == "text":
        if not isinstance(source_data, str):
            raise AgentError("invalid_input", "resume_source.data must be text when type=text")
        return source_data.strip()

    raise AgentError("invalid_input", "resume_source.type must be 'pdf' or 'text'")


def _resolve_jd_text(jd_source: dict[str, Any]) -> str:
    source_type = jd_source.get("type")
    source_data = jd_source.get("data")

    if source_type == "url":
        if not isinstance(source_data, str):
            raise AgentError("invalid_input", "jd_source.data must be URL text when type=url")
        scraped = scrape_job_description(source_data.strip()).strip()
        if len(scraped) < _MIN_TEXT_LENGTH:
            raise AgentError(
                "jd_scrape_failed",
                "Could not read this URL. Please paste the job description text.",
            )
        return scraped

    if source_type == "text":
        if not isinstance(source_data, str):
            raise AgentError("invalid_input", "jd_source.data must be text when type=text")
        return source_data.strip()

    raise AgentError("invalid_input", "jd_source.type must be 'url' or 'text'")


def _validate_and_truncate_inputs(resume_text: str, jd_text: str) -> tuple[str, str]:
    if len(resume_text) < _MIN_TEXT_LENGTH:
        raise AgentError("resume_too_short", "Resume text is too short for analysis.")
    if len(jd_text) < _MIN_TEXT_LENGTH:
        raise AgentError("jd_too_short", "Job description text is too short for analysis.")
    return resume_text[:_MAX_RESUME_CHARS], jd_text[:_MAX_JD_CHARS]


def _build_correction_prompt(raw_response: str) -> str:
    return (
        "Your previous output did not match the required JSON schema for ResumeScoreResult.\n"
        "Return ONLY valid JSON with fields:\n"
        "match_score (0-100 int), grade, summary, matched_skills, missing_skills, "
        "suggestions, jd_key_requirements, ats_risk (low|medium|high), ats_risk_reason.\n\n"
        "Do not include markdown or extra commentary.\n\n"
        f"Previous output:\n{raw_response}"
    )


def _parse_and_validate(raw: str) -> ResumeScoreResult:
    parsed = parse_json_from_response(raw)
    return ResumeScoreResult(**parsed)


def _call_llm_json(prompt: str) -> str:
    """Gemini first (structured JSON); on overload/empty, Groq if configured."""
    try:
        return call_gemini(
            prompt,
            max_tokens=_MAX_TOKENS,
            expect_json=True,
            timeout_seconds=_RESUME_LLM_TIMEOUT,
        )
    except LLMError as exc:
        if exc.code not in _GEMINI_FAILOVER_CODES:
            raise
        logger.warning("resume_scorer: Gemini failed (%s), trying Groq", exc.code)
    return call_groq(
        prompt,
        max_tokens=_MAX_TOKENS,
        expect_json=True,
        timeout_seconds=_RESUME_LLM_TIMEOUT,
    )


def analyze_resume_and_jd(
    resume_source: Any, jd_source: Any, user_id: str
) -> ResumeScoreResult:
    """Analyze resume against JD and return PRD-shaped score result."""
    started_at = time.perf_counter()
    agent_name = "resume_scorer"

    try:
        normalized_resume_source = _normalize_source(resume_source)
        normalized_jd_source = _normalize_source(jd_source)

        resume_text = _resolve_resume_text(normalized_resume_source)
        jd_text = _resolve_jd_text(normalized_jd_source)
        resume_text, jd_text = _validate_and_truncate_inputs(resume_text, jd_text)

        prompt_template = load_prompt("resume_score_v1.txt")
        prompt = prompt_template.format(resume=resume_text, jd=jd_text)
        raw = _call_llm_json(prompt)

        try:
            result = _parse_and_validate(raw)
        except (ValidationError, ValueError):
            correction_prompt = _build_correction_prompt(raw)
            raw_retry = _call_llm_json(correction_prompt)
            result = _parse_and_validate(raw_retry)

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "agent_success",
            extra={
                "agent_name": agent_name,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "score": result.match_score,
                # Token counts are placeholders until router/SDK usage metadata wiring.
                "input_tokens": None,
                "output_tokens": None,
                "success": True,
            },
        )
        return result

    except AgentError:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.warning(
            "agent_expected_failure",
            extra={
                "agent_name": agent_name,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "success": False,
            },
        )
        raise
    except (LLMError, ValidationError, ValueError) as exc:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "agent_unexpected_failure",
            extra={
                "agent_name": agent_name,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "success": False,
            },
        )
        raise exc
