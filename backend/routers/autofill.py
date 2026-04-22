"""POST /api/autofill (PRD Section 12)."""

from uuid import UUID

from fastapi import APIRouter, Depends

from agents.autofill_mapper import AgentError as AutofillAgentError
from agents.autofill_mapper import map_fields_to_profile
from exceptions import JsonHttpError
from middleware.auth import get_current_user
from routers.mock_data import mock_user_profile
from schemas.autofill import AutofillRequest, AutofillResult
from schemas.common import AgentError
from services.llm import LLMError

router = APIRouter(tags=["autofill"])


@router.post("/autofill", response_model=AutofillResult)
def autofill(
    body: AutofillRequest,
    user_id: str = Depends(get_current_user),
) -> AutofillResult:
    """Run autofill mapper (rule-based + LLM fallback on only unmapped fields)."""
    if body.profile is not None:
        profile = body.profile.model_copy(update={"id": UUID(user_id)})
    else:
        profile = mock_user_profile(
            user_id=user_id,
            email="abhinavdave2020@gmail.com",
            full_name="Abhinav Dave",
            onboarding_complete=True,
        )
    try:
        return map_fields_to_profile(body.page_url.strip(), profile)
    except AutofillAgentError as exc:
        raise JsonHttpError(
            422,
            {
                "error": exc.error,
                "message": exc.message,
                "detail": exc.detail,
            },
        ) from exc
    except LLMError as exc:
        raise JsonHttpError(
            503,
            AgentError(
                error=exc.code,
                message=str(exc),
                detail=None,
            ).model_dump(),
        ) from exc
