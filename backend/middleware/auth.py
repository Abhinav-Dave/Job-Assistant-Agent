"""Bearer JWT validation for Supabase access tokens (PRD Section 11)."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt

from settings import get_settings


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
    authorization: Annotated[str | None, Header(description="Bearer access_token")] = None,
) -> str:
    """
    FastAPI dependency: Authorization: Bearer <supabase_jwt> → user_id (UUID string).
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
        )
    token = authorization[len("Bearer ") :].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return verify_jwt(token)
