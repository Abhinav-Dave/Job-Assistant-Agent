"""FormField, FieldMapping, AutofillResult (PRD Section 12)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FormField(BaseModel):
    """Parsed HTML form control (tools/scraper) / internal use."""

    model_config = ConfigDict(extra="forbid")

    field_id: str = Field(min_length=1)
    name: str | None = None
    label: str | None = None
    field_type: str = Field(min_length=1)
    placeholder: str | None = None


class FieldMapping(BaseModel):
    """One mapped field in autofill response."""

    model_config = ConfigDict(extra="forbid")

    field_id: str
    field_label: str
    field_type: str
    profile_key: str
    suggested_value: str
    confidence: float = Field(ge=0.0, le=1.0)


class AutofillResult(BaseModel):
    """`POST /api/autofill` success payload."""

    model_config = ConfigDict(extra="forbid")

    fill_rate: float = Field(ge=0.0, le=1.0)
    total_fields: int = Field(ge=0)
    mapped_fields: int = Field(ge=0)
    mappings: list[FieldMapping]
    unfilled_fields: list[str]

    @model_validator(mode="after")
    def mapped_vs_total(self) -> AutofillResult:
        if self.mapped_fields > self.total_fields:
            raise ValueError("mapped_fields cannot exceed total_fields")
        return self
