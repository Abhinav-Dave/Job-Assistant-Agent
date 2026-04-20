"""POST/GET/PATCH /api/users (PRD Section 12)."""

from fastapi import APIRouter, Depends, HTTPException

from middleware.auth import get_current_user
from routers.mock_data import mock_user_profile
from schemas.user import CreateUserRequest, UpdateUserRequest, UserProfile

router = APIRouter(tags=["users"])


@router.post("", status_code=201, response_model=UserProfile)
async def create_user(
    body: CreateUserRequest,
    user_id: str = Depends(get_current_user),
) -> UserProfile:
    """Create user profile row after registration — Phase 4 mock."""
    if str(body.id) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Profile id must match authenticated user",
        )
    return mock_user_profile(
        user_id=user_id,
        email=str(body.email),
        full_name=body.full_name,
        onboarding_complete=False,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(user_id: str = Depends(get_current_user)) -> UserProfile:
    """Current user profile — Phase 4 mock."""
    return mock_user_profile(
        user_id=user_id,
        email="jane@example.com",
        full_name="Jane Smith",
        onboarding_complete=True,
    )


@router.patch("/me", response_model=UserProfile)
async def patch_me(
    _body: UpdateUserRequest,
    user_id: str = Depends(get_current_user),
) -> UserProfile:
    """Update profile — Phase 4 mock (ignores body except validation)."""
    return mock_user_profile(
        user_id=user_id,
        email="jane@example.com",
        full_name="Jane Smith",
        onboarding_complete=True,
    )
