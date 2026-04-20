"""POST /api/resume/analyze (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user

router = APIRouter(tags=["resume"])


@router.post("/analyze")
async def analyze_resume(_user_id: str = Depends(get_current_user)) -> dict:
    """Run resume scorer (stub)."""
    return {
        "match_score": 0,
        "grade": "N/A",
        "summary": "stub",
    }
