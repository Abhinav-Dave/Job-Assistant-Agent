"""
Run from anywhere (uses `backend/.env` and/or repo root `.env`):

  python verify_db.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

_BACKEND = Path(__file__).resolve().parent
_REPO = _BACKEND.parent

# Ensure os.environ is populated before any Settings import (same paths as settings.py)
for _path in (_BACKEND / ".env", _REPO / ".env"):
    if _path.is_file() and _path.stat().st_size == 0:
        print(
            f"Warning: {_path} is empty on disk — save the file in your editor if you have unsaved changes."
        )
    load_dotenv(_path)


def main() -> int:
    try:
        from settings import get_settings
        from services.supabase import get_supabase

        get_settings.cache_clear()
        s = get_settings()
        if not s.supabase_url or not s.supabase_key:
            print(
                "Supabase connectivity check failed: SUPABASE_URL and a key "
                "(SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY) must be set in "
                "backend/.env or the repo root .env (see .env.example)."
            )
            return 1

        result = get_supabase().table("users").select("id").limit(1).execute()
    except Exception as exc:
        print("Supabase connectivity check failed:", exc)
        return 1
    print("Supabase connectivity OK:", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
