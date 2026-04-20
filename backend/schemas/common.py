"""AgentError, HealthCheckResult (PRD Section 12)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AgentError(BaseModel):
    """Standard API error body."""

    model_config = ConfigDict(extra="forbid")

    error: str
    message: str
    detail: str | None = None


class HealthCheckResult(BaseModel):
    """`GET /api/health` payload (PRD Section 12, 17)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]
    database: str
    llm: str
    version: str
    timestamp: datetime
