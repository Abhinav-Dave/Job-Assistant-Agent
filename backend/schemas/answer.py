"""AnswerRequest, AnswerResult (PRD Section 12)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.user import UserProfile


class AnswerRequest(BaseModel):
    """`POST /api/generate/answer` body."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    jd_text: str | None = None
    jd_url: str | None = None
    profile: UserProfile | None = None

    @model_validator(mode="after")
    def jd_source_present(self) -> AnswerRequest:
        has_jd_text = bool(self.jd_text and self.jd_text.strip())
        has_jd_url = bool(self.jd_url and str(self.jd_url).strip())
        if not has_jd_text and not has_jd_url:
            raise ValueError("Must provide jd_text and/or jd_url")
        return self


class AnswerResult(BaseModel):
    """`POST /api/generate/answer` success payload."""

    model_config = ConfigDict(extra="forbid")

    answer: str
    word_count: int = Field(ge=0)
    question: str
