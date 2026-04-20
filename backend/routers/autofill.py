"""POST /api/autofill (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user

router = APIRouter(tags=["autofill"])


@router.post("/autofill")
async def autofill(_user_id: str = Depends(get_current_user)) -> dict:
    """Map profile to form fields (stub)."""
    return {
        "fill_rate": 0.0,
        "total_fields": 0,
        "mapped_fields": 0,
        "mappings": [],
        "unfilled_fields": [],
    }
