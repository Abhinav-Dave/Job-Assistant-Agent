from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from agents import answer_generator
from schemas.user import EducationItem, UserPreferences, UserProfile, WorkHistoryItem
from services.llm import LLMError


def _answer_exact_words(n: int, *, include_i: bool = True) -> str:
    """Deterministic prose of length n words (default includes first-person I)."""
    if include_i:
        return " ".join(["I"] + [f"word{x}" for x in range(n - 1)])
    return " ".join([f"word{x}" for x in range(n)])


def _build_profile() -> UserProfile:
    now = datetime.now(timezone.utc)
    return UserProfile(
        id=uuid4(),
        email="jane@example.com",
        full_name="Jane Smith",
        phone="416-555-0100",
        location="Toronto, ON",
        linkedin_url="https://linkedin.com/in/janesmith",
        portfolio_url="https://github.com/janesmith",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "CI/CD"],
        preferences=UserPreferences(
            desired_roles=["Backend Engineer"],
            target_industries=["Fintech"],
            remote_preference="hybrid",
            salary_min=90000,
        ),
        work_history=[
            WorkHistoryItem(
                id=uuid4(),
                company="Acme Corp",
                role="Software Engineer",
                start_date="2022-01",
                end_date=None,
                is_current=True,
                bullets=[
                    "Built REST APIs with FastAPI and PostgreSQL.",
                    "Reduced API latency by 40% through indexing work.",
                    "Led CI/CD deployment improvements.",
                ],
                display_order=0,
            ),
            WorkHistoryItem(
                id=uuid4(),
                company="Beta Labs",
                role="Junior Developer",
                start_date="2020-06",
                end_date="2021-12",
                is_current=False,
                bullets=["Maintained internal tools.", "Improved test coverage."],
                display_order=1,
            ),
        ],
        education=[
            EducationItem(
                id=uuid4(),
                institution="University of Toronto",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                graduation_year=2020,
                gpa="3.8",
                display_order=0,
            )
        ],
        onboarding_complete=True,
        created_at=now,
        updated_at=now,
    )


def test_generate_tailored_answer_success_and_cleanup(monkeypatch) -> None:
    captured = {"prompt": ""}

    def _fake_call(prompt: str, **_kwargs):
        captured["prompt"] = prompt
        body = _answer_exact_words(120)
        return f"Great question! Here is your answer:\n```markdown\n{body}\n```"

    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "Q:{question}\nP:{profile}\nJ:{jd}")
    monkeypatch.setattr(answer_generator, "call_gemini", _fake_call)
    monkeypatch.setattr(answer_generator, "call_groq", lambda *_a, **_k: "unused")

    profile = _build_profile()
    result = answer_generator.generate_tailored_answer(
        question="Why are you a good fit for this role?",
        user_profile=profile,
        jd_text="A" * 4100,
    )

    assert 100 <= result.word_count <= 300
    assert "Great question!" not in result.answer
    assert "```" not in result.answer
    assert result.question == "Why are you a good fit for this role?"
    assert "Acme Corp" in captured["prompt"]
    assert "A" * 3000 in captured["prompt"]
    assert "A" * 3001 not in captured["prompt"]


def test_generate_tailored_answer_too_short(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "{question} {profile} {jd}")
    monkeypatch.setattr(answer_generator, "call_gemini", lambda *_a, **_k: "I built APIs.")
    monkeypatch.setattr(answer_generator, "call_groq", lambda *_a, **_k: _answer_exact_words(120))
    result = answer_generator.generate_tailored_answer(
        question="Tell us about your impact",
        user_profile=_build_profile(),
        jd_text="B" * 300,
    )
    assert result.word_count >= 100


def test_generate_tailored_answer_retries_then_succeeds(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "{question} {profile} {jd}")
    monkeypatch.setattr(answer_generator, "call_groq", lambda *_a, **_k: "unused")

    calls = {"count": 0}

    def _fake_call(*_a, **_k):
        calls["count"] += 1
        if calls["count"] == 1:
            return "I built APIs."
        return _answer_exact_words(120)

    monkeypatch.setattr(answer_generator, "call_gemini", _fake_call)

    result = answer_generator.generate_tailored_answer(
        question="Tell us about your impact",
        user_profile=_build_profile(),
        jd_text="B" * 300,
    )
    assert calls["count"] == 2
    assert result.word_count >= 100


def test_generate_tailored_answer_retries_on_llm_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "{question} {profile} {jd}")
    monkeypatch.setattr(answer_generator, "call_groq", lambda *_a, **_k: "unused")

    calls = {"count": 0}

    def _fake_call(*_a, **_k):
        calls["count"] += 1
        if calls["count"] < 3:
            raise LLMError("llm_unavailable", "503 backend busy")
        return _answer_exact_words(120)

    monkeypatch.setattr(answer_generator, "call_gemini", _fake_call)

    result = answer_generator.generate_tailored_answer(
        question="Why should we hire you?",
        user_profile=_build_profile(),
        jd_text="C" * 300,
    )
    assert calls["count"] == 3
    assert result.word_count >= 100


def test_generate_tailored_answer_fallback_when_llm_fails(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "{question} {profile} {jd}")
    monkeypatch.setattr(
        answer_generator,
        "call_gemini",
        lambda *_a, **_k: (_ for _ in ()).throw(
            LLMError("llm_unavailable", "503 service unavailable")
        ),
    )

    monkeypatch.setattr(
        answer_generator,
        "call_groq",
        lambda *_a, **_k: (_ for _ in ()).throw(
            LLMError("llm_unavailable", "503 service unavailable")
        ),
    )

    result = answer_generator.generate_tailored_answer(
        question="Why should we hire you?",
        user_profile=_build_profile(),
        jd_text="D" * 300,
    )
    assert result.word_count >= 100
    assert "I" in result.answer


def test_generate_tailored_answer_quality_failure_on_banned_phrase(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "{question} {profile} {jd}")
    banned = " ".join(
        ["I am a highly motivated engineer with production experience."] * 18
    )
    monkeypatch.setattr(answer_generator, "call_gemini", lambda *_a, **_k: banned)
    monkeypatch.setattr(
        answer_generator,
        "call_groq",
        lambda *_a, **_k: _answer_exact_words(120),
    )

    result = answer_generator.generate_tailored_answer(
        question="Why should we hire you?",
        user_profile=_build_profile(),
        jd_text="C" * 300,
    )
    assert result.word_count >= 100
    assert "highly motivated" not in result.answer.lower()


def test_generate_tailored_answer_jd_too_short(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "call_groq", lambda *_a, **_k: "unused")
    with pytest.raises(answer_generator.AgentError) as exc:
        answer_generator.generate_tailored_answer(
            question="Why this role?",
            user_profile=_build_profile(),
            jd_text="",
        )

    assert exc.value.error == "jd_too_short"


def test_resolve_word_limits_question_overrides(monkeypatch) -> None:
    assert answer_generator.resolve_word_limits("Please respond in 80 words about teamwork.") == (
        60,
        80,
    )


def test_generate_tailored_answer_retries_on_too_long(monkeypatch) -> None:
    monkeypatch.setattr(answer_generator, "load_prompt", lambda _n: "{question} {profile} {jd}")
    monkeypatch.setattr(answer_generator, "call_groq", lambda *_a, **_k: "unused")
    calls = {"count": 0}

    def _fake_call(*_a, **_k):
        calls["count"] += 1
        if calls["count"] == 1:
            return _answer_exact_words(350)
        return _answer_exact_words(120)

    monkeypatch.setattr(answer_generator, "call_gemini", _fake_call)
    result = answer_generator.generate_tailored_answer(
        question="Why should we hire you?",
        user_profile=_build_profile(),
        jd_text="C" * 300,
    )
    assert calls["count"] == 2
    assert result.word_count <= 300
    assert answer_generator.LAST_PROVIDER_USED == "gemini"
