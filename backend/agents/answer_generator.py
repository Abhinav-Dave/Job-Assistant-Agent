"""Tailored answer generator flow (PRD Section 7, Section 12)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from schemas.answer import AnswerResult
from schemas.user import UserProfile
from services.llm import LLMError, call_gemini, call_groq, load_prompt

logger = logging.getLogger(__name__)

_MIN_WORD_COUNT = 100
_DEFAULT_MAX_WORD_COUNT = 300
_MAX_JD_CHARS = 3000
# ~1 token ≈ 0.75 words for English prose; 300 words ≈ 400 tokens; leave headroom.
_MAX_TOKENS = 480
_MAX_SKILLS = 15
_MAX_ROLES = 2
_MAX_BULLETS_PER_ROLE = 3
_MAX_GENERATION_ATTEMPTS = 3
_LLM_TIMEOUT_SECONDS = 18
_SERIOUS_LLM_ERROR_CODES = {"llm_unavailable", "llm_empty_response"}

# Set by generate_tailored_answer for logging / smoke tests (not API contract).
LAST_PROVIDER_USED: str | None = None
LAST_WORD_LIMIT_MAX: int | None = None

_PREAMBLE_PATTERNS = (
    r"^\s*(here(?:'s| is)\s+(?:a|your)\s+answer:?\s*)",
    r"^\s*(certainly!?|great question!?|absolutely!?|sure!?)(\s|,)+",
)

_META_LINE_PATTERNS = (
    r"^\s*this answer\b.*$",
    r"^\s*as an ai\b.*$",
)

_BANNED_PHRASES = (
    "i am a highly motivated",
    "i am passionate about",
    "i excel at",
    "i am a team player",
    "as an ai",
)


class AgentError(Exception):
    """Structured agent exception for predictable failures."""

    def __init__(self, error: str, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict[str, str | None]:
        return {"error": self.error, "message": self.message, "detail": self.detail}


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def _most_recent_roles(work_history: list[Any]) -> list[Any]:
    return sorted(work_history, key=lambda role: role.display_order)[:_MAX_ROLES]


def _build_profile_summary(user_profile: UserProfile) -> dict[str, Any]:
    recent_roles = _most_recent_roles(user_profile.work_history)
    role_summaries: list[str] = []
    key_experience: list[str] = []

    for role in recent_roles:
        role_summaries.append(f"{role.role} at {role.company}")
        key_experience.extend(
            [bullet.strip() for bullet in role.bullets[:_MAX_BULLETS_PER_ROLE] if bullet.strip()]
        )

    education = (
        f"{user_profile.education[0].degree} from {user_profile.education[0].institution}"
        if user_profile.education
        else None
    )

    return {
        "name": user_profile.full_name,
        "most_recent_role": role_summaries[0] if role_summaries else None,
        "recent_roles": role_summaries,
        "key_experience": key_experience,
        "skills": user_profile.skills[:_MAX_SKILLS],
        "education": education,
        "location": user_profile.location,
    }


def clean_answer(raw: str) -> str:
    """Strip preambles/meta/markdown and normalize answer text."""
    cleaned = raw.strip()

    for pattern in _PREAMBLE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"```(?:\w+)?", "", cleaned)
    cleaned = re.sub(r"[*_#`>\-]{1,3}", "", cleaned)

    lines = cleaned.splitlines()
    filtered_lines = []
    for line in lines:
        if any(re.match(pattern, line, flags=re.IGNORECASE) for pattern in _META_LINE_PATTERNS):
            continue
        filtered_lines.append(line)

    cleaned = " ".join(filtered_lines)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _validate_inputs(question: str, jd_text: str) -> tuple[str, str]:
    question_clean = _normalize_text(question)
    jd_clean = _normalize_text(jd_text)

    if not question_clean:
        raise AgentError("invalid_input", "Question is required.")
    if not jd_clean:
        raise AgentError("jd_too_short", "Job description text is too short for answer generation.")

    return question_clean, jd_clean[:_MAX_JD_CHARS]


def _env_max_word_default() -> int:
    raw = (os.environ.get("ANSWER_MAX_WORDS") or "").strip()
    if raw.isdigit():
        return max(50, min(int(raw), 600))
    return _DEFAULT_MAX_WORD_COUNT


def resolve_word_limits(question: str) -> tuple[int, int]:
    """Return (min_words, max_words). Defaults: 100 min, 300 max (env ANSWER_MAX_WORDS overrides max)."""
    env_default_max = _env_max_word_default()
    m = re.search(r"\b(\d{1,3})\s*words?\b", question.lower())
    if m:
        cap = int(m.group(1))
        cap = max(30, min(cap, 500))
        max_words = cap
        if max_words < _MIN_WORD_COUNT:
            min_words = max(15, int(max_words * 0.75))
        else:
            min_words = _MIN_WORD_COUNT
        if min_words > max_words:
            min_words = max(10, max_words - 5)
        return (min_words, max_words)
    return (_MIN_WORD_COUNT, env_default_max)


def _truncate_to_max_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _validate_answer_quality(answer: str, min_words: int, max_words: int) -> int:
    word_count = len(answer.split())
    if word_count < min_words:
        raise AgentError("answer_too_short", "Generated answer was too short. Please try again.")
    if word_count > max_words:
        raise AgentError("answer_too_long", "Generated answer exceeded the word limit. Please tighten.")

    lowered = answer.lower()
    if any(phrase in lowered for phrase in _BANNED_PHRASES):
        raise AgentError(
            "answer_quality_failed",
            "Generated answer did not meet quality requirements. Please try again.",
            detail="Contains banned generic phrases.",
        )
    if re.search(r"\bi\b", lowered) is None:
        raise AgentError(
            "answer_quality_failed",
            "Generated answer did not meet quality requirements. Please try again.",
            detail="Answer must be written in first person.",
        )
    return word_count


def _build_regeneration_prompt(
    base_prompt: str,
    prior_answer: str,
    error: AgentError,
    attempt_number: int,
    min_words: int,
    max_words: int,
) -> str:
    if error.error == "answer_too_long":
        length_line = (
            f"- Cut the answer to at most {max_words} words. Remove repetition; keep strongest JD + profile proof.\n"
        )
    elif error.error == "answer_too_short":
        length_line = f"- Expand to at least {min_words} words without exceeding {max_words}.\n"
    else:
        length_line = (
            f"- Stay between {min_words} and {max_words} words (hard cap {max_words}; recruiter-friendly pacing).\n"
        )

    return (
        f"{base_prompt}\n\n"
        "REWRITE INSTRUCTIONS (must follow):\n"
        f"- Your previous attempt failed quality check: {error.error}.\n"
        f"- This is rewrite attempt {attempt_number}/{_MAX_GENERATION_ATTEMPTS}.\n"
        f"{length_line}"
        "- Write in first person with concrete examples.\n"
        "- Use specific profile details and JD requirements.\n"
        "- No preamble, no markdown, no meta commentary.\n"
        "- Avoid banned phrases: 'I am a highly motivated', 'I am passionate about', "
        "'I excel at', 'I am a team player'.\n\n"
        f"Previous answer:\n{prior_answer}"
    )


def _extract_jd_signals(jd_text: str, limit: int = 6) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+/.-]{2,}", jd_text)
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "you",
        "your",
        "role",
        "team",
        "that",
        "this",
        "are",
        "will",
        "our",
        "from",
        "have",
        "using",
        "build",
        "experience",
        "years",
    }
    seen: set[str] = set()
    signals: list[str] = []
    for token in tokens:
        cleaned = token.strip().lower()
        if cleaned in stop_words or cleaned in seen:
            continue
        seen.add(cleaned)
        signals.append(token)
        if len(signals) >= limit:
            break
    return signals


def _build_fallback_answer(
    question: str, profile_summary: dict[str, Any], jd_text: str, max_words: int
) -> str:
    name = profile_summary.get("name") or "I"
    recent_roles = profile_summary.get("recent_roles") or []
    most_recent_role = profile_summary.get("most_recent_role") or (
        recent_roles[0] if recent_roles else "software engineering role"
    )
    key_experience = profile_summary.get("key_experience") or []
    skills = profile_summary.get("skills") or []
    education = profile_summary.get("education") or "my technical training"
    jd_signals = _extract_jd_signals(jd_text)

    exp_sentence = (
        "In my recent work, I " + "; I ".join(key_experience[:3]) + "."
        if key_experience
        else "In my recent work, I have focused on delivering reliable backend systems that scale."
    )
    skills_sentence = (
        "I bring hands-on strength in "
        + ", ".join(str(skill) for skill in skills[:6])
        + ", and I apply these tools pragmatically based on product goals."
        if skills
        else "I have practical backend engineering skills that I apply based on product and reliability priorities."
    )
    jd_sentence = (
        "The role's emphasis on "
        + ", ".join(jd_signals)
        + " matches the systems and outcomes I have already delivered."
        if jd_signals
        else "The requirements in this job description align directly with the backend and platform work I have been doing."
    )

    answer = (
        f"{question} I believe I am a strong fit because my recent experience as a {most_recent_role} "
        "has been focused on shipping production backend features with measurable business impact. "
        f"{exp_sentence} "
        f"{skills_sentence} "
        "I also work closely with product, design, and frontend partners, so I can translate ambiguous requirements "
        "into clean APIs, clear delivery plans, and stable releases.\n\n"
        f"{jd_sentence} "
        "When I design backend services, I prioritize maintainability first, then performance and observability, "
        "because fast iteration and reliable operations matter as much as initial implementation speed. "
        "I am comfortable owning schema decisions, API contracts, and deployment quality end to end, including "
        "testing, rollout safety, and post-release monitoring.\n\n"
        f"I would bring that same ownership mindset here, along with the foundation from {education}. "
        "I am confident I can contribute quickly, improve system reliability, and help the team ship features "
        "that are both technically sound and valuable for users."
    )
    return _truncate_to_max_words(clean_answer(answer), max_words)


def _try_provider(
    provider_name: str,
    provider_call: Any,
    base_prompt: str,
    min_words: int,
    max_words: int,
) -> tuple[str, int]:
    current_prompt = base_prompt
    last_error: AgentError | LLMError | None = None

    for attempt in range(1, _MAX_GENERATION_ATTEMPTS + 1):
        raw = ""
        try:
            raw = provider_call(current_prompt)
            answer = clean_answer(raw)
            word_count = _validate_answer_quality(answer, min_words, max_words)
            return answer, word_count
        except AgentError as exc:
            last_error = exc
            prior_for_rewrite = clean_answer(raw) if raw else ""
            if (
                exc.error
                in {"answer_too_short", "answer_too_long", "answer_quality_failed"}
                and attempt < _MAX_GENERATION_ATTEMPTS
            ):
                current_prompt = _build_regeneration_prompt(
                    base_prompt=base_prompt,
                    prior_answer=prior_for_rewrite,
                    error=exc,
                    attempt_number=attempt + 1,
                    min_words=min_words,
                    max_words=max_words,
                )
                continue
            break
        except LLMError as exc:
            last_error = exc
            # For transient provider errors, allow retry before trying next provider.
            if attempt < _MAX_GENERATION_ATTEMPTS and exc.code in _SERIOUS_LLM_ERROR_CODES:
                continue
            break

    if isinstance(last_error, LLMError):
        raise last_error
    if isinstance(last_error, AgentError):
        raise last_error
    raise AgentError(
        "answer_generation_failed",
        f"{provider_name} did not produce a usable answer.",
    )


def _generate_valid_answer(
    prompt: str,
    question: str,
    profile_summary: dict[str, Any],
    jd_text: str,
    min_words: int,
    max_words: int,
) -> tuple[str, int, str]:
    provider_errors: list[str] = []
    serious_provider_outage = False

    def _gemini_call(prompt_text: str) -> str:
        return call_gemini(
            prompt_text,
            max_tokens=_MAX_TOKENS,
            expect_json=False,
            timeout_seconds=_LLM_TIMEOUT_SECONDS,
        )

    try:
        answer, wc = _try_provider(
            "gemini", _gemini_call, prompt, min_words, max_words
        )
        return answer, wc, "gemini"
    except LLMError as exc:
        provider_errors.append(f"gemini:{exc.code}:{exc}")
        if exc.code in _SERIOUS_LLM_ERROR_CODES:
            serious_provider_outage = True
    except AgentError as exc:
        provider_errors.append(f"gemini:{exc.error}:{exc.message}")

    def _groq_call(prompt_text: str) -> str:
        return call_groq(
            prompt_text,
            max_tokens=_MAX_TOKENS,
            expect_json=False,
            timeout_seconds=_LLM_TIMEOUT_SECONDS,
        )

    try:
        answer, wc = _try_provider("groq", _groq_call, prompt, min_words, max_words)
        return answer, wc, "groq"
    except LLMError as exc:
        provider_errors.append(f"groq:{exc.code}:{exc}")
        if exc.code in _SERIOUS_LLM_ERROR_CODES:
            serious_provider_outage = True
    except AgentError as exc:
        provider_errors.append(f"groq:{exc.error}:{exc.message}")

    if serious_provider_outage:
        fallback = _build_fallback_answer(question, profile_summary, jd_text, max_words)
        return fallback, len(fallback.split()), "fallback"

    raise AgentError(
        "answer_generation_failed",
        "Could not generate a high-quality answer from available models.",
        detail=" | ".join(provider_errors[-4:]) if provider_errors else None,
    )


def generate_tailored_answer(
    question: str, user_profile: UserProfile, jd_text: str
) -> AnswerResult:
    """Generate a tailored answer using profile summary + JD context."""
    global LAST_PROVIDER_USED, LAST_WORD_LIMIT_MAX
    started_at = time.perf_counter()
    agent_name = "answer_generator"
    user_id = str(getattr(user_profile, "id", "")) or None

    try:
        clean_question, truncated_jd = _validate_inputs(question, jd_text)
        min_words, max_words = resolve_word_limits(clean_question)
        LAST_WORD_LIMIT_MAX = max_words
        profile_summary = _build_profile_summary(user_profile)
        prompt_template = load_prompt("answer_gen_v1.txt")
        prompt = prompt_template.format(
            question=clean_question,
            profile=json.dumps(profile_summary, ensure_ascii=True, separators=(",", ":")),
            jd=truncated_jd,
        )
        answer, word_count, llm_provider = _generate_valid_answer(
            prompt, clean_question, profile_summary, truncated_jd, min_words, max_words
        )
        LAST_PROVIDER_USED = llm_provider

        result = AnswerResult(answer=answer, word_count=word_count, question=clean_question)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "agent_success",
            extra={
                "agent_name": agent_name,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "word_count": result.word_count,
                "llm_provider": llm_provider,
                "word_limit_max": max_words,
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
                "word_count": 0,
                "success": False,
            },
        )
        raise
    except LLMError as exc:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "agent_unexpected_failure",
            extra={
                "agent_name": agent_name,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "word_count": 0,
                "success": False,
            },
        )
        raise exc
