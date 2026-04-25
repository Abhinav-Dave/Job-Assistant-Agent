"""CRUD /api/applications (PRD Section 12)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import Response

from middleware.auth import get_current_user
from schemas.application import (
    Application,
    ApplicationStatus,
    CreateApplicationRequest,
    ResumeScoreReport,
    UpdateApplicationRequest,
    UpsertResumeScoreReportRequest,
)
from services.supabase import get_supabase

router = APIRouter(tags=["applications"])


def _fetch_application_by_id(user_id: str, application_id: str) -> Application | None:
    response = (
        get_supabase()
        .table("applications")
        .select("*")
        .eq("id", application_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return Application(**rows[0])


@router.get("", response_model=list[Application])
async def list_applications(
    user_id: str = Depends(get_current_user),
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
) -> list[Application]:
    """List applications for authenticated user."""
    query = (
        get_supabase()
        .table("applications")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
    )
    if status_filter is not None:
        query = query.eq("status", status_filter.value)
    response = query.execute()
    return [Application(**row) for row in (response.data or [])]


@router.post("", status_code=201, response_model=Application)
async def create_application(
    body: CreateApplicationRequest,
    user_id: str = Depends(get_current_user),
) -> Application:
    """Create application for authenticated user."""
    payload = body.model_dump(exclude_none=True)
    payload["user_id"] = user_id
    created = get_supabase().table("applications").insert(payload).execute().data or []
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create application")
    return Application(**created[0])


@router.patch("/{application_id}", response_model=Application)
async def update_application(
    application_id: str,
    body: UpdateApplicationRequest,
    user_id: str = Depends(get_current_user),
) -> Application:
    """Update one application for authenticated user."""
    existing = _fetch_application_by_id(user_id, application_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Application not found")

    # mode="json" converts date/datetime values to JSON-serializable forms
    # before passing payload to postgrest/httpx.
    updates = body.model_dump(exclude_unset=True, exclude_none=True, mode="json")
    if not updates:
        return existing
    updated_rows = (
        get_supabase()
        .table("applications")
        .update(updates)
        .eq("id", application_id)
        .eq("user_id", user_id)
        .execute()
        .data
        or []
    )
    if not updated_rows:
        raise HTTPException(status_code=500, detail="Failed to update application")
    return Application(**updated_rows[0])


@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    user_id: str = Depends(get_current_user),
) -> Response:
    """Delete one application for authenticated user."""
    get_supabase().table("applications").delete().eq("id", application_id).eq("user_id", user_id).execute()
    return Response(status_code=204)


@router.get("/{application_id}/score-report", response_model=ResumeScoreReport | None)
async def get_application_score_report(
    application_id: str,
    user_id: str = Depends(get_current_user),
) -> ResumeScoreReport | None:
    """Return persisted score report for this application, if present."""
    existing = _fetch_application_by_id(user_id, application_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Application not found")
    rows = (
        get_supabase()
        .table("application_score_reports")
        .select("*")
        .eq("application_id", application_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    return ResumeScoreReport(**rows[0])


@router.put("/{application_id}/score-report", response_model=ResumeScoreReport)
async def upsert_application_score_report(
    application_id: str,
    body: UpsertResumeScoreReportRequest,
    user_id: str = Depends(get_current_user),
) -> ResumeScoreReport:
    """Persist or update score report for this application."""
    existing = _fetch_application_by_id(user_id, application_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Application not found")
    payload = {
        "application_id": application_id,
        "user_id": user_id,
        **body.model_dump(),
    }
    rows = (
        get_supabase()
        .table("application_score_reports")
        .upsert(payload, on_conflict="application_id")
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to persist score report")
    return ResumeScoreReport(**rows[0])
