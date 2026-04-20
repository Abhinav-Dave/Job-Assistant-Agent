"""CRUD /api/applications (PRD Section 12)."""

from fastapi import APIRouter, Depends
from starlette.responses import Response

from middleware.auth import get_current_user

router = APIRouter(tags=["applications"])


@router.get("")
async def list_applications(
    user_id: str = Depends(get_current_user),
    status: str | None = None,
) -> list:
    """List applications for the authenticated user (stub)."""
    return []


@router.post("", status_code=201)
async def create_application(user_id: str = Depends(get_current_user)) -> dict:
    """Create application (stub)."""
    return {"id": "00000000-0000-0000-0000-000000000000", "user_id": user_id}


@router.patch("/{application_id}")
async def update_application(
    application_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Update application (stub)."""
    return {"id": application_id, "user_id": user_id}


@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    _user_id: str = Depends(get_current_user),
) -> Response:
    """Delete application (stub)."""
    return Response(status_code=204)
