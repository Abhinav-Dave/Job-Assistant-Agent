"""Load backend environment (see repo `.env.example` and `docs/setup-external-services.md`)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent


def _env_file_paths() -> tuple[str, ...] | None:
    """Prefer `backend/.env`, then repo root `.env` (same vars as `.env.example`)."""
    paths = [p for p in (_BACKEND_DIR / ".env", _REPO_ROOT / ".env") if p.is_file()]
    return tuple(str(p) for p in paths) if paths else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file_paths(),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    google_gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="GenerativeModel id; override with env GEMINI_MODEL.",
    )
    gemini_model_fallback: str = Field(
        default="gemini-2.5-flash-lite",
        description="Second model on Gemini 429/503 overload (avoid gemini-2.0-flash: deprecated for new API keys). Empty disables.",
    )

    environment: str = "development"
    log_level: str = "INFO"

    @property
    def supabase_key(self) -> str:
        """Prefer service role for server-side queries (RLS bypass when needed)."""
        return self.supabase_service_role_key or self.supabase_anon_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
