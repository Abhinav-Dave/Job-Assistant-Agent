"""Autofill mapper — map_fields_to_profile() (PRD Section 7)."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from typing import Any, Callable

from schemas.autofill import AutofillResult, FieldMapping, FormField
from schemas.user import UserProfile
from services.llm import JSONParseError, LLMError, call_gemini, load_prompt, parse_json_from_response
from tools.scraper import scrape_form_fields, scrape_form_fields_interactive

logger = logging.getLogger(__name__)

_RULE_CONFIDENCE = 0.95
_MIN_SUGGEST_CONFIDENCE = 0.50
_AUTO_FILL_CONFIDENCE = 0.85
_LLM_MAX_TOKENS = 800
_MAX_LLM_FIELDS = 60

ProfileExtractor = Callable[[UserProfile], str | None]

_JUNK_LABEL_SNIPPETS = (
    "copy link",
    "share",
    "oda-work-summary",
    "oda work summary",
    "chat",
    "assistant",
    "help",
    "search for a job",
)
_MEANINGFUL_HINTS = (
    "name",
    "first name",
    "last name",
    "legal first",
    "legal last",
    "preferred name",
    "given name",
    "family name",
    "email",
    "phone",
    "linkedin",
    "website",
    "portfolio",
    "github",
    "city",
    "location",
    "resume",
    "cover letter",
    "experience",
    "address",
    "postal",
    "zip",
    "state",
    "province",
    "country",
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


def _extract_first_name(profile: UserProfile) -> str | None:
    parts = profile.full_name.split()
    return parts[0].strip() if parts else None


def _extract_last_name(profile: UserProfile) -> str | None:
    parts = profile.full_name.split()
    return " ".join(parts[1:]).strip() if len(parts) > 1 else None


def _extract_city(profile: UserProfile) -> str | None:
    if profile.city:
        return profile.city.strip() or None
    location = (profile.location or "").strip()
    if not location:
        return None
    return location.split(",")[0].strip() or None


def _extract_province(profile: UserProfile) -> str | None:
    if profile.province:
        return profile.province.strip() or None
    if not profile.location:
        return None
    parts = [p.strip() for p in profile.location.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[1]
    return None


def _extract_country(profile: UserProfile) -> str | None:
    if profile.country:
        return profile.country.strip() or None
    if not profile.location:
        return None
    parts = [p.strip() for p in profile.location.split(",") if p.strip()]
    if len(parts) >= 3:
        return parts[2]
    return None


def _extract_phone_country_code(profile: UserProfile) -> str | None:
    phone = (profile.phone or "").strip()
    if not phone:
        return None
    if phone.startswith("+"):
        digits = []
        for ch in phone[1:]:
            if ch.isdigit() and len(digits) < 3:
                digits.append(ch)
            else:
                break
        if digits:
            return f"+{''.join(digits)}"
    # Default North America code if no explicit + prefix is available.
    return "+1"


def _calculate_years_experience(profile: UserProfile) -> str | None:
    if not profile.work_history:
        return None
    starts: list[datetime] = []
    for item in profile.work_history:
        try:
            starts.append(datetime.strptime(item.start_date, "%Y-%m").replace(tzinfo=UTC))
        except ValueError:
            continue
    if not starts:
        return None
    earliest = min(starts)
    now = datetime.now(UTC)
    years = max(0.0, (now - earliest).days / 365.25)
    return str(int(round(years)))


FIELD_MAP: dict[str, tuple[str | None, ProfileExtractor | None]] = {
    "first name": ("full_name", _extract_first_name),
    "first": ("full_name", _extract_first_name),
    "firstname": ("full_name", _extract_first_name),
    "given name": ("full_name", _extract_first_name),
    "given": ("full_name", _extract_first_name),
    "forename": ("full_name", _extract_first_name),
    "legal first name": ("full_name", _extract_first_name),
    "last name": ("full_name", _extract_last_name),
    "last": ("full_name", _extract_last_name),
    "lastname": ("full_name", _extract_last_name),
    "family name": ("full_name", _extract_last_name),
    "surname": ("full_name", _extract_last_name),
    "legal last name": ("full_name", _extract_last_name),
    "full name": ("full_name", lambda p: p.full_name),
    "name": ("full_name", lambda p: p.full_name),
    "email": ("email", lambda p: p.email),
    "email address": ("email", lambda p: p.email),
    "phone": ("phone", lambda p: p.phone),
    "phone number": ("phone", lambda p: p.phone),
    "mobile": ("phone", lambda p: p.phone),
    "country phone code": ("phone", _extract_phone_country_code),
    "phone country code": ("phone", _extract_phone_country_code),
    "country code": ("phone", _extract_phone_country_code),
    "phone extension": (None, None),
    "extension": (None, None),
    "city": ("location", _extract_city),
    "address": ("address_line1", lambda p: p.address_line1),
    "address line 1": ("address_line1", lambda p: p.address_line1),
    "street address": ("address_line1", lambda p: p.address_line1),
    "address line 2": ("address_line2", lambda p: p.address_line2),
    "apartment": ("address_line2", lambda p: p.address_line2),
    "suite": ("address_line2", lambda p: p.address_line2),
    "province": ("province", _extract_province),
    "state": ("province", _extract_province),
    "country": ("country", _extract_country),
    "postal code": ("postal_code", lambda p: p.postal_code),
    "zip": ("postal_code", lambda p: p.postal_code),
    "zip code": ("postal_code", lambda p: p.postal_code),
    "location": ("location", lambda p: p.location),
    "linkedin": ("linkedin_url", lambda p: p.linkedin_url),
    "linkedin url": ("linkedin_url", lambda p: p.linkedin_url),
    "portfolio": ("portfolio_url", lambda p: p.portfolio_url),
    "website": ("portfolio_url", lambda p: p.portfolio_url),
    "github": ("portfolio_url", lambda p: p.portfolio_url),
    "years of experience": ("work_history", _calculate_years_experience),
    "experience": ("work_history", _calculate_years_experience),
    "resume": (None, None),
    "cover letter": (None, None),
}

_NON_AUTOFILL_TYPES = {"file", "password", "checkbox", "radio"}


def _normalize_field_text(field: FormField) -> str:
    source = " ".join(
        part for part in (field.label, field.name, field.placeholder, field.field_id) if part
    ).lower()
    source = source.replace("_", " ").replace("-", " ")
    source = re.sub(r"\s+", " ", source)
    return source.strip()


def _is_meaningful_field(field: FormField) -> bool:
    normalized = _normalize_field_text(field)
    if not normalized:
        return False
    if any(snippet in normalized for snippet in _JUNK_LABEL_SNIPPETS):
        return False
    if field.field_type.lower() in {"hidden", "submit", "button", "image", "reset"}:
        return False
    if any(hint in normalized for hint in _MEANINGFUL_HINTS):
        return True
    # Keep non-trivial textual prompts (e.g. custom questions) for LLM fallback.
    alpha_count = sum(1 for ch in normalized if ch.isalpha())
    return alpha_count >= 6


def _meaningful_fields_or_error(fields: list[FormField], page_url: str) -> list[FormField]:
    meaningful = [field for field in fields if _is_meaningful_field(field)]
    if meaningful:
        return meaningful
    if fields:
        raise AgentError(
            "ats_page_not_ready",
            "Form controls were found, but no meaningful application fields are accessible yet.",
            detail=(
                "This ATS page may require additional navigation, session state, or anti-bot challenge "
                f"before real fields appear. url={page_url}"
            ),
        )
    raise AgentError("no_fields_detected", "No form fields found on this page.")


def _rule_key_for_field(field: FormField) -> str | None:
    normalized = _normalize_field_text(field)
    if not normalized:
        return None
    if normalized in FIELD_MAP:
        return normalized
    matches = [candidate for candidate in FIELD_MAP if candidate and candidate in normalized]
    if not matches:
        return None
    return max(matches, key=len)


def _profile_key_descriptions() -> dict[str, str]:
    return {
        "full_name": "Candidate full legal/professional name",
        "email": "Primary email address",
        "phone": "Primary phone number",
        "location": "Current city/region",
        "address_line1": "Street address line 1",
        "address_line2": "Street address line 2 (apt/suite)",
        "city": "Current city",
        "province": "State or province",
        "country": "Current country",
        "postal_code": "Postal code / ZIP code",
        "linkedin_url": "LinkedIn profile URL",
        "portfolio_url": "Portfolio or GitHub URL",
        "work_history": "Career history and total years of experience",
        "skills": "Top skills list",
    }


def _value_to_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value)


def _build_mapping(
    *,
    field: FormField,
    profile_key: str,
    suggested_value: str,
    confidence: float,
) -> FieldMapping:
    return FieldMapping(
        field_id=field.field_id,
        field_label=field.label or field.name or field.field_id,
        field_type=field.field_type,
        profile_key=profile_key,
        suggested_value=suggested_value,
        confidence=confidence,
    )


def _rule_based_mappings(
    fields: list[FormField], user_profile: UserProfile
) -> tuple[list[FieldMapping], list[FormField], list[str]]:
    mappings: list[FieldMapping] = []
    unmapped: list[FormField] = []
    unknown_labels: list[str] = []

    for field in fields:
        if field.field_type.lower() in _NON_AUTOFILL_TYPES:
            unknown_labels.append(field.label or field.name or field.field_id)
            continue

        rule_key = _rule_key_for_field(field)
        if not rule_key:
            unmapped.append(field)
            continue

        profile_key, extractor = FIELD_MAP[rule_key]
        if profile_key is None or extractor is None:
            unknown_labels.append(field.label or field.name or field.field_id)
            continue

        suggested = _value_to_string(extractor(user_profile))
        if not suggested:
            unknown_labels.append(field.label or field.name or field.field_id)
            continue

        mappings.append(
            _build_mapping(
                field=field,
                profile_key=profile_key,
                suggested_value=suggested,
                confidence=_RULE_CONFIDENCE,
            )
        )

    return mappings, unmapped, unknown_labels


def _llm_fallback_mappings(
    unmapped_fields: list[FormField], user_profile: UserProfile
) -> tuple[list[FieldMapping], list[str]]:
    if not unmapped_fields:
        return [], []

    prompt_template = load_prompt("autofill_v1.txt")
    fields_payload = [field.model_dump() for field in unmapped_fields[:_MAX_LLM_FIELDS]]
    prompt = prompt_template.format(
        fields=json.dumps(fields_payload, ensure_ascii=True),
        profile_keys=json.dumps(_profile_key_descriptions(), ensure_ascii=True),
    )
    raw = call_gemini(prompt, max_tokens=_LLM_MAX_TOKENS, expect_json=True)
    payload = (raw or "").strip()
    try:
        parsed: Any = json.loads(payload)
    except json.JSONDecodeError:
        try:
            parsed = parse_json_from_response(raw)
        except JSONParseError:
            # Degrade gracefully when model returns clipped/non-JSON output.
            return [], [field.label or field.name or field.field_id for field in unmapped_fields]

    if isinstance(parsed, dict):
        parsed = parsed.get("mappings", parsed.get("fields", []))
    if not isinstance(parsed, list):
        raise AgentError("invalid_llm_response", "Autofill model returned an invalid JSON shape.")

    field_by_id = {field.field_id: field for field in unmapped_fields}
    llm_mappings: list[FieldMapping] = []
    unknown_labels: list[str] = []

    for item in parsed:
        if not isinstance(item, dict):
            continue
        field_id = str(item.get("field_id", "")).strip()
        profile_key = item.get("profile_key")
        suggested_value = item.get("suggested_value")
        confidence_raw = item.get("confidence", 0.0)

        field = field_by_id.get(field_id)
        if field is None:
            continue
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        profile_key_str = _value_to_string(profile_key)
        suggested_value_str = _value_to_string(suggested_value)
        if (
            not profile_key_str
            or not suggested_value_str
            or confidence < _MIN_SUGGEST_CONFIDENCE
        ):
            unknown_labels.append(field.label or field.name or field.field_id)
            continue

        llm_mappings.append(
            _build_mapping(
                field=field,
                profile_key=profile_key_str,
                suggested_value=suggested_value_str,
                confidence=max(0.0, min(1.0, confidence)),
            )
        )

    mapped_ids = {mapping.field_id for mapping in llm_mappings}
    for field in unmapped_fields:
        if field.field_id not in mapped_ids:
            unknown_labels.append(field.label or field.name or field.field_id)

    return llm_mappings, unknown_labels


def map_fields_to_profile(page_url: str, user_profile: UserProfile) -> AutofillResult:
    """Map scraped fields to profile values using rule-first strategy + LLM fallback."""
    started_at = time.perf_counter()
    agent_name = "autofill_mapper"
    user_id = str(getattr(user_profile, "id", "")) or None

    try:
        fields = scrape_form_fields(page_url)
        try:
            fields = _meaningful_fields_or_error(fields, page_url)
        except AgentError as exc:
            if exc.error not in {"ats_page_not_ready", "no_fields_detected"}:
                raise
            # Direct interactive filler mode recovery:
            # force browser interaction/progression and retry field extraction.
            interactive_fields = scrape_form_fields_interactive(page_url)
            if not interactive_fields:
                raise exc
            try:
                fields = _meaningful_fields_or_error(interactive_fields, page_url)
            except AgentError:
                # Preserve original ATS diagnosis when fallback also fails.
                raise exc

        rule_mappings, unmapped_fields, rule_unknowns = _rule_based_mappings(fields, user_profile)
        llm_mappings, llm_unknowns = _llm_fallback_mappings(unmapped_fields, user_profile)
        all_mappings = rule_mappings + llm_mappings

        auto_fill = [m for m in all_mappings if m.confidence >= _AUTO_FILL_CONFIDENCE]
        suggest = [
            m
            for m in all_mappings
            if _MIN_SUGGEST_CONFIDENCE <= m.confidence < _AUTO_FILL_CONFIDENCE
        ]
        # Keep unknown labels aligned to original field labels for stable UI messaging.
        unknown_labels = list(dict.fromkeys(rule_unknowns + llm_unknowns))
        mapped_count = len(auto_fill) + len(suggest)
        fill_rate = mapped_count / len(fields) if fields else 0.0

        result = AutofillResult(
            fill_rate=fill_rate,
            total_fields=len(fields),
            mapped_fields=mapped_count,
            mappings=all_mappings,
            unfilled_fields=unknown_labels,
        )

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            "agent_success",
            extra={
                "agent_name": agent_name,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "total_fields": len(fields),
                "mapped_fields": mapped_count,
                "auto_fill_fields": len(auto_fill),
                "suggest_fields": len(suggest),
                "unknown_fields": len(unknown_labels),
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
    except (LLMError, ValueError) as exc:
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
