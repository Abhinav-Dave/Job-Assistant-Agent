"""POST/GET/PATCH /api/users (PRD Section 12)."""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from middleware.auth import get_current_user
from schemas.user import CreateUserRequest, EducationItem, UpdateUserRequest, UserProfile, WorkHistoryItem
from services.supabase import get_supabase

router = APIRouter(tags=["users"])

_USER_BASE_FIELDS = {
    "email",
    "full_name",
    "phone",
    "location",
    "address_line1",
    "address_line2",
    "city",
    "province",
    "country",
    "postal_code",
    "linkedin_url",
    "portfolio_url",
    "skills",
    "preferences",
    "onboarding_complete",
}


def _get_auth_defaults(user_id: str) -> tuple[str, str]:
    fallback_email = f"user-{user_id[:8]}@example.com"
    fallback_name = "New User"
    try:
        auth_user = get_supabase().auth.admin.get_user_by_id(user_id).user
        email = auth_user.email or fallback_email
        metadata = auth_user.user_metadata or {}
        full_name = (
            metadata.get("full_name")
            or metadata.get("name")
            or (email.split("@", 1)[0] if "@" in email else fallback_name)
        )
        return email, full_name
    except Exception:
        return fallback_email, fallback_name


def _fetch_single_user_row(user_id: str) -> dict[str, Any] | None:
    response = get_supabase().table("users").select("*").eq("id", user_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None


def _safe_update_user_row(user_id: str, updates: dict[str, Any]) -> None:
    """Update `users` while tolerating missing columns in older local schemas."""
    pending = dict(updates)
    if not pending:
        return
    while pending:
        try:
            get_supabase().table("users").update(pending).eq("id", user_id).execute()
            return
        except Exception as exc:
            message = str(exc).lower()
            is_missing_column_error = (
                ("column" in message and "does not exist" in message)
                or ("could not find" in message and "schema cache" in message)
            )
            if not is_missing_column_error:
                raise
            removed_any = False
            for key in list(pending.keys()):
                if key.lower() in message:
                    pending.pop(key, None)
                    removed_any = True
            if not removed_any:
                raise


def _ensure_user_profile_row(user_id: str) -> dict[str, Any]:
    existing = _fetch_single_user_row(user_id)
    if existing is not None:
        return existing

    email, full_name = _get_auth_defaults(user_id)
    try:
        inserted = (
            get_supabase()
            .table("users")
            .insert(
                {
                    "id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "skills": [],
                    "preferences": {},
                    "onboarding_complete": False,
                }
            )
            .execute()
        )
    except Exception as exc:
        message = str(exc).lower()
        # Stale or forged JWTs can reference users absent in auth/users FK tables.
        if "foreign key" in message or "violates foreign key constraint" in message:
            raise HTTPException(
                status_code=401,
                detail="Authenticated user record is missing. Log out and sign in again.",
            ) from exc
        raise
    inserted_rows = inserted.data or []
    if not inserted_rows:
        raise HTTPException(status_code=500, detail="Failed to create profile row")
    return inserted_rows[0]


def _fetch_profile(user_id: str) -> UserProfile:
    user_row = _ensure_user_profile_row(user_id)
    work_rows = (
        get_supabase()
        .table("work_history")
        .select("*")
        .eq("user_id", user_id)
        .order("display_order", desc=False)
        .execute()
        .data
        or []
    )
    education_rows = (
        get_supabase()
        .table("education")
        .select("*")
        .eq("user_id", user_id)
        .order("display_order", desc=False)
        .execute()
        .data
        or []
    )

    work_history = [
        WorkHistoryItem(
            id=row["id"],
            company=row["company"],
            role=row["role"],
            start_date=row["start_date"],
            end_date=row.get("end_date"),
            is_current=bool(row.get("is_current", False)),
            bullets=list(row.get("bullets") or []),
            display_order=int(row.get("display_order") or 0),
        )
        for row in work_rows
    ]
    education = [
        EducationItem(
            id=row["id"],
            institution=row["institution"],
            degree=row["degree"],
            field_of_study=row.get("field_of_study"),
            graduation_year=row.get("graduation_year"),
            gpa=Decimal(str(row["gpa"])) if row.get("gpa") is not None else None,
            display_order=int(row.get("display_order") or 0),
        )
        for row in education_rows
    ]

    return UserProfile(
        id=user_row["id"],
        email=user_row["email"],
        full_name=user_row["full_name"],
        phone=user_row.get("phone"),
        location=user_row.get("location"),
        address_line1=user_row.get("address_line1"),
        address_line2=user_row.get("address_line2"),
        city=user_row.get("city"),
        province=user_row.get("province"),
        country=user_row.get("country"),
        postal_code=user_row.get("postal_code"),
        linkedin_url=user_row.get("linkedin_url"),
        portfolio_url=user_row.get("portfolio_url"),
        skills=list(user_row.get("skills") or []),
        preferences=user_row.get("preferences") or {},
        work_history=work_history,
        education=education,
        onboarding_complete=bool(user_row.get("onboarding_complete", False)),
        created_at=user_row["created_at"],
        updated_at=user_row["updated_at"],
    )


@router.post("", status_code=201, response_model=UserProfile)
async def create_user(
    body: CreateUserRequest,
    user_id: str = Depends(get_current_user),
) -> UserProfile:
    """Create or update user profile row after registration."""
    if str(body.id) != user_id:
        raise HTTPException(status_code=403, detail="Profile id must match authenticated user")

    existing = _fetch_single_user_row(user_id)
    payload = {
        "id": user_id,
        "email": str(body.email),
        "full_name": body.full_name,
        "skills": [],
        "preferences": {},
        "onboarding_complete": False,
    }
    if existing is None:
        get_supabase().table("users").insert(payload).execute()
    else:
        _safe_update_user_row(user_id, {"email": payload["email"], "full_name": payload["full_name"]})
    return _fetch_profile(user_id)


@router.get("/me", response_model=UserProfile)
async def get_me(user_id: str = Depends(get_current_user)) -> UserProfile:
    """Current user profile."""
    return _fetch_profile(user_id)


@router.patch("/me", response_model=UserProfile)
async def patch_me(
    body: UpdateUserRequest,
    user_id: str = Depends(get_current_user),
) -> UserProfile:
    """Persist profile fields and return latest profile."""
    _ensure_user_profile_row(user_id)
    updates = body.model_dump(exclude_unset=True)

    base_updates = {key: updates[key] for key in updates.keys() if key in _USER_BASE_FIELDS}
    if base_updates:
        _safe_update_user_row(user_id, base_updates)

    if body.work_history is not None:
        get_supabase().table("work_history").delete().eq("user_id", user_id).execute()
        work_history = body.work_history
        if work_history:
            get_supabase().table("work_history").insert(
                [
                    {
                        "id": str(item.id),
                        "user_id": user_id,
                        "company": item.company,
                        "role": item.role,
                        "start_date": item.start_date,
                        "end_date": item.end_date,
                        "is_current": item.is_current,
                        "bullets": item.bullets,
                        "display_order": item.display_order,
                    }
                    for item in work_history
                ]
            ).execute()

    if body.education is not None:
        get_supabase().table("education").delete().eq("user_id", user_id).execute()
        education = body.education
        if education:
            get_supabase().table("education").insert(
                [
                    {
                        "id": str(item.id),
                        "user_id": user_id,
                        "institution": item.institution,
                        "degree": item.degree,
                        "field_of_study": item.field_of_study,
                        "graduation_year": item.graduation_year,
                        "gpa": float(item.gpa) if item.gpa is not None else None,
                        "display_order": item.display_order,
                    }
                    for item in education
                ]
            ).execute()

    return _fetch_profile(user_id)
