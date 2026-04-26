"""POST /api/autofill (PRD Section 12)."""

from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID

from fastapi import APIRouter, Depends
from postgrest.exceptions import APIError as PostgrestAPIError

from agents.autofill_mapper import AgentError as AutofillAgentError
from agents.autofill_mapper import map_fields_to_profile
from exceptions import JsonHttpError
from middleware.auth import get_current_user
from routers.mock_data import mock_user_profile
from schemas.autofill import AutofillRequest, AutofillResult
from schemas.application import Application, ApplicationStatus
from schemas.common import AgentError
from services.llm import LLMError
from services.supabase import get_supabase

router = APIRouter(tags=["autofill"])
logger = logging.getLogger(__name__)

_FINALIZED_APPLICATION_STATUSES = {
    ApplicationStatus.submitted.value,
    ApplicationStatus.response_received.value,
    ApplicationStatus.interview_requested.value,
    ApplicationStatus.interview_completed.value,
    ApplicationStatus.onsite_requested.value,
    ApplicationStatus.offer_received.value,
    ApplicationStatus.rejected.value,
    ApplicationStatus.withdrawn.value,
}


def _normalize_job_url(page_url: str) -> str:
    parsed = urlparse(page_url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"
    query_pairs = sorted(parse_qsl(parsed.query, keep_blank_values=False))
    query = urlencode(query_pairs, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def _infer_company_from_url(page_url: str) -> str:
    parsed = urlparse(page_url)
    host = parsed.netloc.lower().removeprefix("www.")
    root = (host.split(".")[0] if host else "") or "unknown"
    return root.replace("-", " ").replace("_", " ").title()


def _fetch_applications_for_user(user_id: str) -> list[Application]:
    rows = (
        get_supabase()
        .table("applications")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
        .data
        or []
    )
    return [Application(**row) for row in rows]


def _upsert_application_from_mapping_preview(user_id: str, page_url: str) -> tuple[str, str, str | None]:
    normalized_target = _normalize_job_url(page_url)
    existing = next(
        (
            application
            for application in _fetch_applications_for_user(user_id)
            if application.jd_url and _normalize_job_url(application.jd_url) == normalized_target
        ),
        None,
    )

    if existing is None:
        create_payload = {
            "user_id": user_id,
            "company": _infer_company_from_url(page_url),
            "role": "Application in progress",
            "jd_url": page_url,
            "status": ApplicationStatus.in_progress.value,
            "date_applied": None,
            "notes": "[mapping_preview][in_progress] Added automatically after successful mapping preview.",
        }
        try:
            created_rows = (
                get_supabase()
                .table("applications")
                .insert(create_payload)
                .execute()
                .data
                or []
            )
        except PostgrestAPIError as exc:
            if exc.code != "23514":
                raise
            # Backward compatibility: if the status constraint migration is not yet
            # applied, fallback to saved while preserving in-progress intent in notes.
            fallback_payload = {**create_payload, "status": ApplicationStatus.saved.value}
            created_rows = (
                get_supabase()
                .table("applications")
                .insert(fallback_payload)
                .execute()
                .data
                or []
            )
        if not created_rows:
            raise RuntimeError("Failed to create tracker application after mapping preview.")
        created = Application(**created_rows[0])
        return "created", created.id.__str__(), None

    if existing.status in _FINALIZED_APPLICATION_STATUSES:
        return "unchanged", existing.id.__str__(), None

    if existing.status == ApplicationStatus.in_progress.value:
        return "unchanged", existing.id.__str__(), None

    update_payload = {
        "status": ApplicationStatus.in_progress.value,
        "jd_url": existing.jd_url or page_url,
        "notes": (
            f"{(existing.notes or '').strip()}\n"
            "[mapping_preview][in_progress] Mapping preview re-run."
        ).strip(),
    }
    try:
        updated_rows = (
            get_supabase()
            .table("applications")
            .update(update_payload)
            .eq("id", existing.id.__str__())
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
    except PostgrestAPIError as exc:
        if exc.code != "23514":
            raise
        fallback_payload = {**update_payload, "status": ApplicationStatus.saved.value}
        updated_rows = (
            get_supabase()
            .table("applications")
            .update(fallback_payload)
            .eq("id", existing.id.__str__())
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
    if not updated_rows:
        raise RuntimeError("Failed to update tracker application after mapping preview.")
    updated = Application(**updated_rows[0])
    return "updated", updated.id.__str__(), None


@router.post("/autofill", response_model=AutofillResult)
def autofill(
    body: AutofillRequest,
    user_id: str = Depends(get_current_user),
) -> AutofillResult:
    """Run autofill mapper (rule-based + LLM fallback on only unmapped fields)."""
    trimmed_url = body.page_url.strip()
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
        result = map_fields_to_profile(trimmed_url, profile)
    except AutofillAgentError as exc:
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
    tracker_sync = "unchanged"
    tracker_sync_message: str | None = None
    tracker_application_id: str | None = None
    try:
        tracker_sync, tracker_application_id, tracker_sync_message = _upsert_application_from_mapping_preview(
            user_id=user_id,
            page_url=trimmed_url,
        )
    except Exception as exc:  # pragma: no cover - defensive logging for runtime DB errors
        logger.exception("mapping_preview_tracker_sync_failed", extra={"user_id": user_id, "page_url": trimmed_url})
        tracker_sync = "failed"
        tracker_sync_message = "Mapping completed, but job was not added to tracker."

    return result.model_copy(
        update={
            "tracker_sync": tracker_sync,
            "tracker_sync_message": tracker_sync_message,
            "tracker_application_id": tracker_application_id,
        }
    )
