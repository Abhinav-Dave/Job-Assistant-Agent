"""POST /api/generate/answer (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user
from schemas.answer import AnswerRequest, AnswerResult

router = APIRouter(tags=["answers"])


@router.post("/generate/answer", response_model=AnswerResult)
async def generate_answer(
    body: AnswerRequest,
    user_id: str = Depends(get_current_user),
) -> AnswerResult:
    """Tailored answer — Phase 4 mock."""
    _ = user_id
    q = body.question
    return AnswerResult(
        answer=(
            "Throughout my two years at Acme Corp, I've built production APIs and "
            "collaborated across teams — a strong fit for this role."
        ),
        word_count=287,
        question=q,
    )
