"""LLM service helpers for Gemini (and optional Groq fallback)."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from settings import get_settings

logger = logging.getLogger(__name__)
_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_TIMEOUT_SECONDS = 30


class LLMError(RuntimeError):
    """Raised when an LLM call fails in an expected way."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class JSONParseError(ValueError):
    """Raised when no valid JSON can be extracted from model output."""


class PromptLoadError(FileNotFoundError):
    """Raised when prompt files are missing or invalid."""


def _timeout_seconds() -> int:
    raw = os.getenv("LLM_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT_SECONDS)).strip()
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else _DEFAULT_TIMEOUT_SECONDS


def _build_gemini_model(api_key: str, model_name: str):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    return genai, genai.GenerativeModel(model_name)


def _build_groq_client(api_key: str):
    from groq import Groq

    return Groq(api_key=api_key)


def load_prompt(filename: str) -> str:
    """Load a text prompt from `backend/prompts` safely."""
    clean_name = (filename or "").strip()
    if not clean_name:
        raise PromptLoadError("Prompt filename is required")

    prompts_dir = (Path(__file__).resolve().parent.parent / "prompts").resolve()
    prompt_path = (prompts_dir / clean_name).resolve()

    if prompts_dir not in prompt_path.parents:
        raise PromptLoadError("Prompt path must stay inside backend/prompts")
    if not prompt_path.is_file():
        raise PromptLoadError(f"Prompt not found: {clean_name}")

    return prompt_path.read_text(encoding="utf-8")


def call_gemini(prompt: str, max_tokens: int = 1500) -> str:
    """Send prompt to Gemini and return response text."""
    if not prompt or not prompt.strip():
        raise LLMError("invalid_input", "Prompt must not be empty")
    if max_tokens <= 0:
        raise LLMError("invalid_input", "max_tokens must be > 0")

    settings = get_settings()
    api_key = (settings.google_gemini_api_key or "").strip()
    if not api_key:
        raise LLMError("llm_not_configured", "GOOGLE_GEMINI_API_KEY is not configured")

    model_name = (settings.gemini_model or _DEFAULT_GEMINI_MODEL).strip() or _DEFAULT_GEMINI_MODEL
    timeout_seconds = _timeout_seconds()

    try:
        genai, model = _build_gemini_model(api_key=api_key, model_name=model_name)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
                response_mime_type="application/json",
            ),
            request_options={"timeout": timeout_seconds},
        )
    except Exception as exc:
        logger.warning("Gemini API error: %s", exc, exc_info=False)
        raise LLMError("llm_unavailable", str(exc)) from exc

    try:
        text = (getattr(response, "text", None) or "").strip()
    except Exception as exc:
        logger.warning("Gemini response read error: %s", exc, exc_info=False)
        raise LLMError("llm_empty_response", str(exc)) from exc
    if text:
        return text

    raise LLMError("llm_empty_response", "Gemini returned an empty response")


def call_groq(prompt: str, max_tokens: int = 1500) -> str:
    """Optional fallback using Groq if installed and configured."""
    if not prompt or not prompt.strip():
        raise LLMError("invalid_input", "Prompt must not be empty")
    if max_tokens <= 0:
        raise LLMError("invalid_input", "max_tokens must be > 0")

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise LLMError("groq_not_configured", "GROQ_API_KEY is not configured")

    model_name = os.getenv("GROQ_MODEL", _DEFAULT_GROQ_MODEL).strip() or _DEFAULT_GROQ_MODEL
    try:
        client = _build_groq_client(api_key)
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        content = completion.choices[0].message.content
        text = (content or "").strip()
        if text:
            return text
    except Exception as exc:
        logger.warning("Groq API error: %s", exc, exc_info=False)
        raise LLMError("llm_unavailable", str(exc)) from exc

    raise LLMError("llm_empty_response", "Groq returned an empty response")


def parse_json_from_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from clean/fenced/preamble LLM responses."""
    payload = (raw or "").strip()
    if not payload:
        raise JSONParseError("Response is empty")

    # 1) Direct parse
    try:
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            return parsed
        raise JSONParseError("Expected JSON object at top level")
    except json.JSONDecodeError:
        pass

    # 2) Markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", payload, re.DOTALL | re.IGNORECASE)
    if fence_match:
        fenced = fence_match.group(1).strip()
        try:
            parsed = json.loads(fenced)
            if isinstance(parsed, dict):
                return parsed
            raise JSONParseError("Expected JSON object in code fence")
        except json.JSONDecodeError:
            pass

    # 3) Preamble/suffix content with embedded JSON
    decoder = json.JSONDecoder()
    for idx, char in enumerate(payload):
        if char not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(payload[idx:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    raise JSONParseError(f"Could not extract valid JSON from response: {payload[:200]}")


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
        call_gemini('{"ping":"ok"}', max_tokens=16)
        return "reachable"
    except LLMError as e:
        logger.warning("LLM health ping failed: %s", e, exc_info=False)
        return "error"

