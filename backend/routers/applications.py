"""CRUD /api/applications (PRD Section 12)."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from starlette.responses import Response

from middleware.auth import get_current_user
from routers.mock_data import mock_application_row
from schemas.application import (
    Application,
    ApplicationStatus,
    CreateApplicationRequest,
    UpdateApplicationRequest,
)

router = APIRouter(tags=["applications"])

_MOCK_APP_ID = UUID("33333333-3333-3333-3333-333333333333")


@router.get("", response_model=list[Application])
async def list_applications(
    user_id: str = Depends(get_current_user),
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
) -> list[Application]:
    """List applications — Phase 4 mock."""
    row = mock_application_row(app_id=_MOCK_APP_ID, user_id=user_id)
    if status_filter is not None and row.status != status_filter:
        return []
    return [row]


@router.post("", status_code=201, response_model=Application)
async def create_application(
    body: CreateApplicationRequest,
    user_id: str = Depends(get_current_user),
) -> Application:
    """Create application — Phase 4 mock."""
    new_id = uuid4()
    base = mock_application_row(app_id=new_id, user_id=user_id)
    return base.model_copy(
        update={
            "company": body.company,
            "role": body.role,
            "jd_url": body.jd_url,
            "jd_text": body.jd_text,
            "status": body.status,
            "notes": body.notes,
            "date_applied": body.date_applied,
        }
    )


@router.patch("/{application_id}", response_model=Application)
async def update_application(
    application_id: str,
    body: UpdateApplicationRequest,
    user_id: str = Depends(get_current_user),
) -> Application:
    """Update application — Phase 4 mock."""
    _ = user_id
    app_id = UUID(application_id)
    base = mock_application_row(app_id=app_id, user_id=user_id)
    updates: dict = {}
    if body.company is not None:
        updates["company"] = body.company
    if body.role is not None:
        updates["role"] = body.role
    if body.jd_url is not None:
        updates["jd_url"] = body.jd_url
    if body.jd_text is not None:
        updates["jd_text"] = body.jd_text
    if body.status is not None:
        updates["status"] = body.status
    if body.notes is not None:
        updates["notes"] = body.notes
    if body.date_applied is not None:
        updates["date_applied"] = body.date_applied
    if body.last_score is not None:
        updates["last_score"] = body.last_score
    return base.model_copy(update=updates)


@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    _user_id: str = Depends(get_current_user),
) -> Response:
    """Delete application — Phase 4 mock."""
    _ = application_id
    return Response(status_code=204)
