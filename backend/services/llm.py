"""Gemini reachability (PRD Sections 15–17). Phase 6 expands `call_gemini`."""

from __future__ import annotations

import logging

from settings import get_settings

logger = logging.getLogger(__name__)


def check_llm_reachable() -> str:
    """
    Lightweight ping for health checks. Returns:
    `not_configured` (no API key), `reachable`, or `error`.
    """
    settings = get_settings()
    key = (settings.google_gemini_api_key or "").strip()
    if not key:
        return "not_configured"

    try:
        import google.generativeai as genai

        genai.configure(api_key=key)
        model_name = (settings.gemini_model or "gemini-2.5-flash").strip()
        model = genai.GenerativeModel(model_name)
        model.generate_content(
            "Reply with the single word: ok",
            generation_config=genai.GenerationConfig(max_output_tokens=16),
        )
        return "reachable"
    except Exception as e:
        logger.warning("LLM health ping failed: %s", e, exc_info=False)
        return "error"


def call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    """Placeholder for Phase 6 — raises if used before implementation."""
    raise NotImplementedError("call_gemini is implemented in Phase 6")

