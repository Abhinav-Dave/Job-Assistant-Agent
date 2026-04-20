"""Pydantic schemas (PRD Section 9, Phase 3)."""

from schemas.answer import AnswerRequest, AnswerResult
from schemas.application import (
    Application,
    ApplicationStatus,
    CreateApplicationRequest,
    UpdateApplicationRequest,
)
from schemas.autofill import AutofillRequest, AutofillResult, FieldMapping, FormField
from schemas.common import AgentError, HealthCheckResult
from schemas.resume import ResumeScoreRequest, ResumeScoreResult
from schemas.feedback import FeedbackLoggedResult, FeedbackRequest
from schemas.user import (
    CreateUserRequest,
    EducationItem,
    UpdateUserRequest,
    UserPreferences,
    UserProfile,
    WorkHistoryItem,
)

__all__ = [
    "AgentError",
    "AnswerRequest",
    "AnswerResult",
    "Application",
    "ApplicationStatus",
    "AutofillRequest",
    "AutofillResult",
    "CreateApplicationRequest",
    "CreateUserRequest",
    "EducationItem",
    "FeedbackLoggedResult",
    "FeedbackRequest",
    "FieldMapping",
    "FormField",
    "HealthCheckResult",
    "ResumeScoreRequest",
    "ResumeScoreResult",
    "UpdateApplicationRequest",
    "UpdateUserRequest",
    "UserPreferences",
    "UserProfile",
    "WorkHistoryItem",
]
