"""
Phase 2 acceptance checks: Supabase query + JWT auth on a protected route.
Loads `backend/.env` and repo root `.env`. Does not print secrets.

  python verify_phase2.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from jose import jwt

_BACKEND = Path(__file__).resolve().parent
_REPO = _BACKEND.parent

def _load_env() -> None:
    for path in (_BACKEND / ".env", _REPO / ".env"):
        if path.is_file() and path.stat().st_size == 0:
            print(
                f"Warning: {path} is empty on disk (0 bytes). "
                "If you edited .env in the editor, save the file, then run this script again."
            )
        load_dotenv(path)


_load_env()


def main() -> int:
    from fastapi.testclient import TestClient

    from settings import get_settings
    from services.supabase import get_supabase, reset_client

    get_settings.cache_clear()
    reset_client()

    settings = get_settings()

    # 1) Database
    if not settings.supabase_url or not settings.supabase_key:
        print("FAIL: Supabase URL/key missing (check backend/.env or root .env).")
        return 1
    try:
        get_supabase().table("users").select("id").limit(1).execute()
    except Exception as exc:
        print("FAIL: Supabase query:", exc)
        return 1
    print("OK: Supabase `users` query succeeded.")

    # 2) JWT middleware (uses same secret as Supabase Auth)
    if not settings.supabase_jwt_secret:
        print("FAIL: SUPABASE_JWT_SECRET missing.")
        return 1

    test_sub = "00000000-0000-0000-0000-000000000001"
    token = jwt.encode(
        {"sub": test_sub, "aud": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )

    import main

    client = TestClient(main.app)
    r = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        print("FAIL: GET /api/users/me with valid JWT:", r.status_code, r.text)
        return 1
    body = r.json()
    if body.get("id") != test_sub:
        print("FAIL: response id mismatch:", body)
        return 1
    print("OK: Protected route accepts Bearer JWT (user id round-trip).")

    r401 = client.get("/api/users/me")
    if r401.status_code != 401:
        print("FAIL: expected 401 without Authorization, got", r401.status_code)
        return 1
    print("OK: Protected route returns 401 without token.")

    rh = client.get("/api/health")
    if rh.status_code != 200 or rh.json().get("status") != "ok":
        print("FAIL: health check:", rh.status_code, rh.text)
        return 1
    print("OK: GET /api/health returns 200.")

    print("Phase 2 backend checks: ALL PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
