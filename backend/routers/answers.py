"""POST /api/generate/answer (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user

router = APIRouter(tags=["answers"])


@router.post("/generate/answer")
async def generate_answer(_user_id: str = Depends(get_current_user)) -> dict:
    """Generate answer from profile + JD (stub)."""
    return {
        "answer": "",
        "word_count": 0,
        "question": "",
    }
