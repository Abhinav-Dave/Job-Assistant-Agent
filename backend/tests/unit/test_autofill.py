from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from agents import autofill_mapper
from schemas.autofill import FormField
from schemas.user import EducationItem, UserPreferences, UserProfile, WorkHistoryItem
from tools import scraper


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
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        preferences=UserPreferences(
            desired_roles=["Backend Engineer"],
            target_industries=[],
            remote_preference="hybrid",
            salary_min=90000,
        ),
        work_history=[
            WorkHistoryItem(
                id=uuid4(),
                company="Acme Corp",
                role="Software Engineer",
                start_date="2021-01",
                end_date=None,
                is_current=True,
                bullets=["Built APIs", "Improved observability"],
                display_order=0,
            )
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


def test_map_fields_to_profile_rule_based_only(monkeypatch) -> None:
    fields = [
        FormField(field_id="first_name", name="first_name", label="First Name", field_type="text"),
        FormField(field_id="email", name="email", label="Email", field_type="email"),
        FormField(field_id="resume", name="resume", label="Resume", field_type="file"),
    ]
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", lambda _url: fields)

    result = autofill_mapper.map_fields_to_profile("https://jobs.example/apply", _build_profile())

    assert result.total_fields == 3
    assert result.mapped_fields == 2
    assert result.fill_rate == pytest.approx(2 / 3, rel=1e-3)
    assert {m.field_id for m in result.mappings} == {"first_name", "email"}
    assert "Resume" in result.unfilled_fields
    assert all(m.confidence >= 0.85 for m in result.mappings)


def test_map_fields_to_profile_llm_fallback_for_unmapped(monkeypatch) -> None:
    fields = [
        FormField(
            field_id="q_linkedin",
            name="custom_linkedin",
            label="LinkedIn Profile URL",
            field_type="text",
        ),
        FormField(
            field_id="q_summary",
            name="summary",
            label="Professional Summary",
            field_type="textarea",
        ),
    ]
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", lambda _url: fields)
    monkeypatch.setattr(autofill_mapper, "load_prompt", lambda _name: "FIELDS={fields}\nKEYS={profile_keys}")
    monkeypatch.setattr(
        autofill_mapper,
        "call_gemini",
        lambda *_a, **_k: """
[
  {"field_id":"q_linkedin","profile_key":"linkedin_url","suggested_value":"https://linkedin.com/in/janesmith","confidence":0.92},
  {"field_id":"q_summary","profile_key":null,"suggested_value":null,"confidence":0.20}
]
""",
    )

    result = autofill_mapper.map_fields_to_profile("https://jobs.example/custom", _build_profile())

    assert result.total_fields == 2
    assert result.mapped_fields == 1
    assert result.fill_rate == pytest.approx(0.5, rel=1e-3)
    assert len(result.mappings) == 1
    assert result.mappings[0].profile_key == "linkedin_url"
    assert "Professional Summary" in result.unfilled_fields


def test_map_fields_to_profile_with_mocked_http_and_llm(monkeypatch) -> None:
    html = """
<html><body>
  <form>
    <label for="fname">First Name</label><input id="fname" name="fname" type="text" />
    <label for="portfolio_custom">Portfolio Link</label><input id="portfolio_custom" name="portfolio_custom" type="text" />
    <label for="why_us">Why us?</label><textarea id="why_us" name="why_us"></textarea>
  </form>
</body></html>
"""

    class _Resp:
        text = html

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(scraper.httpx, "get", lambda *_a, **_k: _Resp())
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", scraper.scrape_form_fields)
    monkeypatch.setattr(autofill_mapper, "load_prompt", lambda _name: "{fields}\n{profile_keys}")
    monkeypatch.setattr(
        autofill_mapper,
        "call_gemini",
        lambda *_a, **_k: """
[
  {"field_id":"portfolio_custom","profile_key":"portfolio_url","suggested_value":"https://github.com/janesmith","confidence":0.89},
  {"field_id":"why_us","profile_key":null,"suggested_value":null,"confidence":0.11}
]
""",
    )

    result = autofill_mapper.map_fields_to_profile("https://jobs.example/http-mocked", _build_profile())

    assert result.total_fields == 3
    assert result.mapped_fields == 2
    assert {m.field_id for m in result.mappings} == {"fname", "portfolio_custom"}
    assert "Why us?" in result.unfilled_fields


def test_map_fields_to_profile_no_fields_detected(monkeypatch) -> None:
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", lambda _url: [])

    with pytest.raises(autofill_mapper.AgentError) as exc:
        autofill_mapper.map_fields_to_profile("https://jobs.example/empty", _build_profile())
    assert exc.value.error == "no_fields_detected"


def test_map_fields_to_profile_ats_page_not_ready_for_junk_controls(monkeypatch) -> None:
    fields = [
        FormField(field_id="copy_link", name="copy_link", label="Copy Link", field_type="text"),
        FormField(
            field_id="oda_work_summary",
            name="oda_work_summary",
            label="oda-work-summary-text-area|input",
            field_type="textarea",
        ),
    ]
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", lambda _url: fields)

    with pytest.raises(autofill_mapper.AgentError) as exc:
        autofill_mapper.map_fields_to_profile("https://oracle.example/apply", _build_profile())
    assert exc.value.error == "ats_page_not_ready"
    assert "oracle.example" in (exc.value.detail or "")


def test_map_fields_to_profile_recovers_with_interactive_fallback(monkeypatch) -> None:
    initial_fields = [
        FormField(field_id="copy_link", name="copy_link", label="Copy Link", field_type="text"),
    ]
    interactive_fields = [
        FormField(field_id="first_name", name="first_name", label="First Name", field_type="text"),
        FormField(field_id="email", name="email", label="Email", field_type="email"),
    ]
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", lambda _url: initial_fields)
    monkeypatch.setattr(
        autofill_mapper,
        "scrape_form_fields_interactive",
        lambda _url: interactive_fields,
    )

    result = autofill_mapper.map_fields_to_profile("https://workday.example/apply", _build_profile())
    assert result.mapped_fields == 2
    assert result.fill_rate == pytest.approx(1.0, rel=1e-3)


def test_map_fields_to_profile_maps_address_fields(monkeypatch) -> None:
    fields = [
        FormField(field_id="last_name", name="last_name", label="Last Name", field_type="text"),
        FormField(field_id="address1", name="address1", label="Address Line 1", field_type="text"),
        FormField(field_id="postal", name="postal", label="Postal Code", field_type="text"),
        FormField(field_id="province", name="province", label="Province", field_type="text"),
        FormField(field_id="country", name="country", label="Country", field_type="text"),
    ]
    profile = _build_profile().model_copy(
        update={
            "full_name": "Abhinav Dave",
            "address_line1": "16 Kingswood Drive",
            "city": "Brampton",
            "province": "Ontario",
            "country": "Canada",
            "postal_code": "L6V 2T6",
        }
    )
    monkeypatch.setattr(autofill_mapper, "scrape_form_fields", lambda _url: fields)

    result = autofill_mapper.map_fields_to_profile("https://jobs.example/address", profile)
    mapped = {m.field_id: m.suggested_value for m in result.mappings}

    assert mapped["last_name"] == "Dave"
    assert mapped["address1"] == "16 Kingswood Drive"
    assert mapped["postal"] == "L6V 2T6"
    assert mapped["province"] == "Ontario"
    assert mapped["country"] == "Canada"
