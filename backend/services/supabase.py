"""Supabase Python client (PRD Sections 9–10, Phase 2)."""

from supabase import Client, create_client

from settings import get_settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return a singleton Supabase client. Uses `SUPABASE_SERVICE_ROLE_KEY` when set, else anon key."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "Supabase is not configured. Set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY in backend/.env "
                "(see .env.example and docs/setup-external-services.md)."
            )
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def reset_client() -> None:
    """Clear cached client (e.g. for tests)."""
    global _client
    _client = None
    get_settings.cache_clear()
