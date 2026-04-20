"""POST /api/feedback (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user
from schemas.feedback import FeedbackLoggedResult, FeedbackRequest

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=201, response_model=FeedbackLoggedResult)
async def log_feedback(
    body: FeedbackRequest,
    user_id: str = Depends(get_current_user),
) -> FeedbackLoggedResult:
    """Log agent feedback — Phase 4 mock."""
    _ = user_id, body.agent_type, body.rating, body.context
    return FeedbackLoggedResult()
