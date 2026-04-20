"""JWT verification (middleware/auth.py)."""

from jose import jwt

from middleware.auth import verify_jwt
from settings import get_settings


def test_verify_jwt_round_trip(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "unit-test-secret")
    get_settings.cache_clear()
    token = jwt.encode(
        {"sub": "550e8400-e29b-41d4-a716-446655440000", "aud": "authenticated"},
        "unit-test-secret",
        algorithm="HS256",
    )
    assert verify_jwt(token) == "550e8400-e29b-41d4-a716-446655440000"
