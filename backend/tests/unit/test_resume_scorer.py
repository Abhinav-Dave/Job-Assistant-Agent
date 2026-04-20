import json

import pytest

from agents import resume_scorer
from services.llm import LLMError


def _valid_payload(match_score: int = 82) -> dict:
    return {
        "match_score": match_score,
        "grade": "B",
        "summary": "Strong overall fit with minor infra gaps.",
        "matched_skills": ["Python", "SQL", "REST APIs"],
        "missing_skills": ["Kubernetes"],
        "suggestions": ["Add Kubernetes production experience bullets."],
        "jd_key_requirements": ["Python", "SQL", "Kubernetes"],
        "ats_risk": "medium",
        "ats_risk_reason": "Missing one high-frequency keyword.",
    }


def test_analyze_resume_and_jd_text_success(monkeypatch) -> None:
    monkeypatch.setattr(
        resume_scorer,
        "load_prompt",
        lambda _name: "RESUME:\n{resume}\nJD:\n{jd}",
    )
    monkeypatch.setattr(
        resume_scorer,
        "call_gemini",
        lambda *_args, **_kwargs: _valid_payload(),
    )
    monkeypatch.setattr(resume_scorer, "parse_json_from_response", lambda raw: raw)

    result = resume_scorer.analyze_resume_and_jd(
        resume_source={"type": "text", "data": "A" * 180},
        jd_source={"type": "text", "data": "B" * 200},
        user_id="user-1",
    )

    assert result.match_score == 82
    assert result.ats_risk == "medium"


def test_analyze_resume_and_jd_retries_once_on_invalid_parse(monkeypatch) -> None:
    monkeypatch.setattr(resume_scorer, "load_prompt", lambda _name: "{resume} {jd}")

    calls = {"count": 0}

    def _fake_call(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return "not-json"
        return _valid_payload(match_score=91)

    def _fake_parse(raw):
        if isinstance(raw, str):
            raise ValueError("bad parse")
        return raw

    monkeypatch.setattr(resume_scorer, "call_gemini", _fake_call)
    monkeypatch.setattr(resume_scorer, "parse_json_from_response", _fake_parse)

    result = resume_scorer.analyze_resume_and_jd(
        resume_source={"type": "text", "data": "R" * 300},
        jd_source={"type": "text", "data": "J" * 300},
        user_id="user-2",
    )

    assert calls["count"] == 2
    assert result.match_score == 91


def test_analyze_resume_and_jd_pdf_no_text(monkeypatch) -> None:
    monkeypatch.setattr(resume_scorer, "extract_text_from_pdf", lambda _bytes: "")

    with pytest.raises(resume_scorer.AgentError) as exc:
        resume_scorer.analyze_resume_and_jd(
            resume_source={"type": "pdf", "data": b"%PDF-1.7"},
            jd_source={"type": "text", "data": "J" * 200},
            user_id="user-3",
        )

    assert exc.value.error == "pdf_no_text"


def test_analyze_resume_and_jd_jd_scrape_failed(monkeypatch) -> None:
    monkeypatch.setattr(resume_scorer, "scrape_job_description", lambda _url: "tiny")

    with pytest.raises(resume_scorer.AgentError) as exc:
        resume_scorer.analyze_resume_and_jd(
            resume_source={"type": "text", "data": "R" * 200},
            jd_source={"type": "url", "data": "https://example.com/job"},
            user_id="user-4",
        )

    assert exc.value.error == "jd_scrape_failed"


def test_analyze_resume_and_jd_resume_too_short() -> None:
    with pytest.raises(resume_scorer.AgentError) as exc:
        resume_scorer.analyze_resume_and_jd(
            resume_source={"type": "text", "data": "short resume"},
            jd_source={"type": "text", "data": "J" * 300},
            user_id="user-5",
        )
    assert exc.value.error == "resume_too_short"


def test_analyze_resume_and_jd_jd_too_short() -> None:
    with pytest.raises(resume_scorer.AgentError) as exc:
        resume_scorer.analyze_resume_and_jd(
            resume_source={"type": "text", "data": "R" * 300},
            jd_source={"type": "text", "data": "short jd"},
            user_id="user-6",
        )
    assert exc.value.error == "jd_too_short"


def test_analyze_resume_and_jd_falls_back_to_groq_when_gemini_overloaded(monkeypatch) -> None:
    monkeypatch.setattr(
        resume_scorer,
        "load_prompt",
        lambda _name: "RESUME:\n{resume}\nJD:\n{jd}",
    )
    monkeypatch.setattr(
        resume_scorer,
        "call_gemini",
        lambda *_a, **_k: (_ for _ in ()).throw(
            LLMError("llm_unavailable", "503 UNAVAILABLE high demand")
        ),
    )
    monkeypatch.setattr(
        resume_scorer,
        "call_groq",
        lambda *_a, **_k: json.dumps(_valid_payload(match_score=77)),
    )
    monkeypatch.setattr(resume_scorer, "parse_json_from_response", lambda raw: json.loads(raw))

    result = resume_scorer.analyze_resume_and_jd(
        resume_source={"type": "text", "data": "A" * 180},
        jd_source={"type": "text", "data": "B" * 200},
        user_id="user-groq",
    )
    assert result.match_score == 77
