"""POST /api/autofill (PRD Section 12)."""

from fastapi import APIRouter, Depends

from middleware.auth import get_current_user
from schemas.autofill import AutofillRequest, AutofillResult, FieldMapping

router = APIRouter(tags=["autofill"])


@router.post("/autofill", response_model=AutofillResult)
async def autofill(
    body: AutofillRequest,
    user_id: str = Depends(get_current_user),
) -> AutofillResult:
    """Autofill mapper — Phase 4 mock."""
    _ = user_id, body.page_url
    return AutofillResult(
        fill_rate=0.82,
        total_fields=17,
        mapped_fields=14,
        mappings=[
            FieldMapping(
                field_id="FirstName",
                field_label="First Name",
                field_type="text",
                profile_key="full_name",
                suggested_value="Jane",
                confidence=0.97,
            )
        ],
        unfilled_fields=["cover_letter", "salary_expectation_text"],
    )
