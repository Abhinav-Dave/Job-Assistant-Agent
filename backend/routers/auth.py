"""POST /api/auth/verify — validate JWT, return user_id (PRD Section 9)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user

router = APIRouter(tags=["auth"])


@router.post("/auth/verify")
async def verify_session(user_id: str = Depends(get_current_user)) -> dict:
    """Protected: confirms Bearer token and returns authenticated user id."""
    return {"user_id": user_id, "valid": True}
