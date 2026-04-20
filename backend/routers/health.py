"""GET /api/health (PRD Section 12)."""

from datetime import UTC, datetime

from fastapi import APIRouter

from services.supabase import get_supabase

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Public. Pings Supabase when configured."""
    database = "not_configured"
    try:
        get_supabase().table("users").select("id").limit(1).execute()
        database = "connected"
    except RuntimeError:
        database = "not_configured"
    except Exception:
        database = "error"

    return {
        "status": "ok",
        "database": database,
        "llm": "unknown",
        "version": "1.0.0",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
