"""Bearer JWT validation for Supabase access tokens (PRD Section 11)."""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from settings import get_settings

# `HTTPBearer` registers OpenAPI security so `/docs` "Authorize" sends `Authorization: Bearer …`.
_bearer = HTTPBearer(auto_error=False)


def verify_jwt(token: str) -> str:
    """
    Validate a Supabase JWT and return auth user id (`sub`).
    Raises HTTPException 401 on failure.
    """
    settings = get_settings()
    secret = settings.supabase_jwt_secret
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_JWT_SECRET is not configured",
        )
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {e}") from e

    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="Token missing user ID")
    return user_id


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    """
    FastAPI dependency: Authorization: Bearer <supabase_jwt> → user_id (UUID string).
    Use `/docs` → **Authorize** → paste the JWT only (no `Bearer ` prefix).
    """
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_jwt(creds.credentials)


def try_get_user_id_from_authorization(authorization: str | None) -> str | None:
    """For request logging: return `sub` when the Bearer token is valid, else None."""
    if authorization is None or not authorization.startswith("Bearer "):
        return None
    token = authorization[len("Bearer ") :].strip()
    if not token:
        return None
    try:
        return verify_jwt(token)
    except HTTPException:
        return None
