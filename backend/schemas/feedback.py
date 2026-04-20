"""Agent feedback request (PRD Section 12)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FeedbackLoggedResult(BaseModel):
    """`POST /api/feedback` success payload."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["logged"] = "logged"


class FeedbackRequest(BaseModel):
    """`POST /api/feedback` body."""

    model_config = ConfigDict(extra="forbid")

    agent_type: str = Field(min_length=1)
    rating: int = Field(description="Typically 1 (up) or -1 (down)")
    context: dict[str, Any] = Field(default_factory=dict)
