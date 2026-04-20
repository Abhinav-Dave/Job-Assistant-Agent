"""GET/POST/PATCH /api/users (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user

router = APIRouter(tags=["users"])


@router.post("", status_code=201)
async def create_user(user_id: str = Depends(get_current_user)) -> dict:
    """Create user profile row after registration (stub)."""
    return {
        "id": user_id,
        "email": "",
        "full_name": "",
        "onboarding_complete": False,
    }


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)) -> dict:
    """Current user profile (stub)."""
    return {"id": user_id, "onboarding_complete": False}


@router.patch("/me")
async def patch_me(user_id: str = Depends(get_current_user)) -> dict:
    """Update profile (stub)."""
    return {"id": user_id, "onboarding_complete": False}
