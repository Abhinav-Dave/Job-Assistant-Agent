"""
Print a **development-only** JWT you can pass as `Authorization: Bearer <token>`.

This backend validates tokens the same way Supabase Auth does: HS256 signed with
`SUPABASE_JWT_SECRET`, payload must include `sub` (auth user UUID) and
`aud: "authenticated"`.

**Do not use** `SUPABASE_ANON_KEY` or `SUPABASE_SERVICE_ROLE_KEY` as Bearer —
those are Supabase API keys, not user access tokens.

**Production-like token:** sign in via the app (or Supabase Auth) and copy
`session.access_token` from the client.

Usage (from `backend/`, after `.env` is loaded the same way as the app):

  python mint_dev_jwt.py
  python mint_dev_jwt.py 550e8400-e29b-41d4-a716-446655440000

Then:

  curl.exe -H "Authorization: Bearer <paste>" http://127.0.0.1:8000/api/users/me
"""

from __future__ import annotations

import sys

from jose import jwt


def main() -> int:
    from settings import get_settings

    # Same env file merge order as `settings.Settings` (no duplicate dotenv precedence bugs).
    get_settings.cache_clear()
    settings = get_settings()
    secret = (settings.supabase_jwt_secret or "").strip()
    if not secret:
        print("Error: SUPABASE_JWT_SECRET is missing (backend/.env or repo root .env).", file=sys.stderr)
        return 1

    sub = sys.argv[1] if len(sys.argv) > 1 else "550e8400-e29b-41d4-a716-446655440000"
    token = jwt.encode(
        {"sub": sub, "aud": "authenticated"},
        secret,
        algorithm="HS256",
    )
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
