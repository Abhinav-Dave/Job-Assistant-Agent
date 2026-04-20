"""POST /api/feedback (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=201)
async def log_feedback(_user_id: str = Depends(get_current_user)) -> dict:
    """Log agent feedback (stub)."""
    return {"status": "logged"}
