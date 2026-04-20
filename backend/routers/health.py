"""GET /api/health (PRD Sections 12, 17)."""

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter

from schemas.common import HealthCheckResult
from services.llm import check_llm_reachable
from services.supabase import get_supabase

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResult)
async def health_check() -> HealthCheckResult:
    """Public. Verifies Supabase connectivity and Gemini reachability when configured."""
    database = "not_configured"
    try:
        get_supabase().table("users").select("id").limit(1).execute()
        database = "connected"
    except RuntimeError:
        database = "not_configured"
    except Exception:
        database = "error"

    llm_status = check_llm_reachable()

    overall: Literal["ok", "degraded"] = (
        "ok" if database == "connected" else "degraded"
    )

    return HealthCheckResult(
        status=overall,
        database=database,
        llm=llm_status,
        version="1.0.0",
        timestamp=datetime.now(UTC),
    )
