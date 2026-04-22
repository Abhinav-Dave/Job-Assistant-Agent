"""Phase 4 mock payloads matching PRD Section 12 shapes."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from schemas.application import Application, ApplicationStatus
from schemas.user import EducationItem, UserPreferences, UserProfile, WorkHistoryItem

try:
    from routers.mock_profile_private import get_private_mock_profile_overrides
except Exception:  # pragma: no cover - optional local-only file
    def get_private_mock_profile_overrides() -> dict[str, object]:
        return {}

# Stable UUIDs for nested rows (PRD examples)
_WH_ID = UUID("11111111-1111-1111-1111-111111111111")
_ED_ID = UUID("22222222-2222-2222-2222-222222222222")


def mock_user_profile(*, user_id: str, email: str, full_name: str, onboarding_complete: bool) -> UserProfile:
    """Full `UserProfile` matching PRD `GET /api/users/me` example."""
    uid = UUID(user_id)
    now = datetime.now(UTC)
    created = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
    updated = datetime(2026, 4, 10, 14, 30, tzinfo=UTC)
    profile_data: dict[str, object] = {
        "id": uid,
        "email": email,
        "full_name": full_name,
        "phone": "416-555-0100",
        "location": "Toronto, ON, Canada",
        "address_line1": None,
        "address_line2": None,
        "city": "Toronto",
        "province": "ON",
        "country": "Canada",
        "postal_code": None,
        "linkedin_url": "https://linkedin.com/in/janesmith",
        "portfolio_url": "https://github.com/janesmith",
        "skills": ["Python", "React", "SQL", "FastAPI"],
        "preferences": UserPreferences(
            desired_roles=["Backend Engineer", "ML Engineer"],
            target_industries=[],
            remote_preference="hybrid",
            salary_min=85000,
        ),
        "work_history": [
            WorkHistoryItem(
                id=_WH_ID,
                company="Acme Corp",
                role="Software Engineer",
                start_date="2022-06",
                end_date=None,
                is_current=True,
                bullets=[
                    "Built REST API endpoints serving 50K requests/day using FastAPI and PostgreSQL",
                    "Reduced query latency by 40% via database indexing and query optimization",
                ],
                display_order=0,
            )
        ],
        "education": [
            EducationItem(
                id=_ED_ID,
                institution="University of Toronto",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                graduation_year=2022,
                gpa=Decimal("3.8"),
                display_order=0,
            )
        ],
        "onboarding_complete": onboarding_complete,
        "created_at": created,
        "updated_at": updated if onboarding_complete else now,
    }
    profile_data.update(get_private_mock_profile_overrides())
    return UserProfile(**profile_data)


def mock_application_row(*, app_id: UUID, user_id: str) -> Application:
    uid = UUID(user_id)
    ts = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)
    return Application(
        id=app_id,
        user_id=uid,
        company="Stripe",
        role="Backend Engineer",
        jd_url="https://stripe.com/jobs/123",
        jd_text=None,
        status=ApplicationStatus.submitted,
        notes="Applied via LinkedIn. Recruiter is Sarah Chen.",
        date_applied=ts.date(),
        last_score=None,
        created_at=ts,
        updated_at=ts,
    )
