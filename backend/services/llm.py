"""LLM service helpers for Gemini (and optional Groq fallback)."""

from __future__ import annotations

import json
import logging
import os
import re
import warnings
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


def _build_gemini_clients(api_key: str, model_name: str):
    """Return active Gemini backend tuple."""
    try:
        from google import genai as google_genai

        client = google_genai.Client(api_key=api_key)
        return "google.genai", client, model_name, None
    except ImportError:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import google.generativeai as legacy_genai

        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel(model_name)
        return "google.generativeai", model, model_name, legacy_genai


def _build_groq_client(api_key: str):
    from groq import Groq

    return Groq(api_key=api_key)


def _gemini_model_chain(primary: str, fallback: str) -> list[str]:
    primary_clean = (primary or _DEFAULT_GEMINI_MODEL).strip() or _DEFAULT_GEMINI_MODEL
    out = [primary_clean]
    fb = (fallback or "").strip()
    if fb and fb not in out:
        out.append(fb)
    return out


_GEMINI_RESERVE_LITE = "gemini-2.5-flash-lite"


def _extend_gemini_model_chain(models: list[str]) -> list[str]:
    """Append stable Flash-Lite when chain still references deprecated gemini-2.0-flash* (404 for new keys)."""
    out = list(models)
    if any(m.startswith("gemini-2.0-flash") for m in out) and _GEMINI_RESERVE_LITE not in out:
        out.append(_GEMINI_RESERVE_LITE)
    return out


def _gemini_retryable(exc: BaseException) -> bool:
    """Whether to try the next model in the chain."""
    raw = str(exc)
    msg = raw.upper()
    if (
        "503" in raw
        or "UNAVAILABLE" in msg
        or "429" in raw
        or "RESOURCE_EXHAUSTED" in msg
        or "OVERLOADED" in msg
    ):
        return True
    # e.g. gemini-2.0-flash removed for new API projects — try next model
    return "NO LONGER AVAILABLE" in msg


def _call_gemini_once(
    *,
    api_key: str,
    model_name: str,
    prompt: str,
    max_tokens: int,
    expect_json: bool,
    resolved_timeout_seconds: int,
) -> str:
    try:
        backend, client_or_model, resolved_model_name, legacy_module = _build_gemini_clients(
            api_key=api_key,
            model_name=model_name,
        )
        generation_config_kwargs: dict[str, Any] = {
            "max_output_tokens": max_tokens,
            "temperature": 0.3,
        }
        if expect_json:
            generation_config_kwargs["response_mime_type"] = "application/json"

        if backend == "google.genai":
            response = client_or_model.models.generate_content(
                model=resolved_model_name,
                contents=prompt,
                config=generation_config_kwargs,
            )
        else:
            response = client_or_model.generate_content(
                prompt,
                generation_config=legacy_module.GenerationConfig(**generation_config_kwargs),
                request_options={"timeout": resolved_timeout_seconds},
            )
    except Exception as exc:
        logger.warning("Gemini API error (%s): %s", model_name, exc, exc_info=False)
        raise LLMError("llm_unavailable", str(exc)) from exc

    try:
        text = (getattr(response, "text", None) or "").strip()
    except Exception as exc:
        logger.warning("Gemini response read error: %s", exc, exc_info=False)
        raise LLMError("llm_empty_response", str(exc)) from exc
    if text:
        return text

    raise LLMError("llm_empty_response", "Gemini returned an empty response")


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


def call_gemini(
    prompt: str,
    max_tokens: int = 1500,
    expect_json: bool = True,
    timeout_seconds: int | None = None,
) -> str:
    """Send prompt to Gemini and return response text."""
    if not prompt or not prompt.strip():
        raise LLMError("invalid_input", "Prompt must not be empty")
    if max_tokens <= 0:
        raise LLMError("invalid_input", "max_tokens must be > 0")

    settings = get_settings()
    api_key = (settings.google_gemini_api_key or "").strip()
    if not api_key:
        raise LLMError("llm_not_configured", "GOOGLE_GEMINI_API_KEY is not configured")

    resolved_timeout_seconds = timeout_seconds or _timeout_seconds()
    fb = getattr(settings, "gemini_model_fallback", "") or ""
    models = _extend_gemini_model_chain(_gemini_model_chain(settings.gemini_model, fb))

    last: LLMError | None = None
    for idx, model_name in enumerate(models):
        try:
            return _call_gemini_once(
                api_key=api_key,
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                expect_json=expect_json,
                resolved_timeout_seconds=resolved_timeout_seconds,
            )
        except LLMError as exc:
            if exc.code == "llm_empty_response":
                raise
            last = exc
            # Retry only when failures are likely transient/model-specific; preserve first hard failure.
            if idx < len(models) - 1 and _gemini_retryable(exc):
                logger.warning(
                    "Gemini model %s failed (%s), retrying with %s",
                    model_name,
                    exc,
                    models[idx + 1],
                )
                continue
            raise
    if last:
        raise last
    raise LLMError("llm_unavailable", "No Gemini model configured")


def call_groq(
    prompt: str,
    max_tokens: int = 1500,
    expect_json: bool = False,
    timeout_seconds: int | None = None,
) -> str:
    """Optional fallback using Groq if installed and configured."""
    if not prompt or not prompt.strip():
        raise LLMError("invalid_input", "Prompt must not be empty")
    if max_tokens <= 0:
        raise LLMError("invalid_input", "max_tokens must be > 0")

    settings = get_settings()
    api_key = (
        os.getenv("GROQ_API_KEY", "").strip()
        or os.getenv("groq_api_key", "").strip()
        or getattr(settings, "groq_api_key", "").strip()
    )
    if not api_key:
        raise LLMError("groq_not_configured", "GROQ_API_KEY is not configured")

    model_name = os.getenv("GROQ_MODEL", _DEFAULT_GROQ_MODEL).strip() or _DEFAULT_GROQ_MODEL
    resolved_timeout_seconds = timeout_seconds or _timeout_seconds()
    try:
        client = _build_groq_client(api_key)
        create_kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": max_tokens,
            "timeout": resolved_timeout_seconds,
        }
        if expect_json:
            create_kwargs["response_format"] = {"type": "json_object"}
        completion = client.chat.completions.create(
            **create_kwargs,
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


def _groq_configured() -> bool:
    settings = get_settings()
    return bool(
        os.getenv("GROQ_API_KEY", "").strip()
        or os.getenv("groq_api_key", "").strip()
        or getattr(settings, "groq_api_key", "").strip()
    )


def check_llm_reachable() -> str:
    """
    Lightweight ping for health checks. Returns:
    `not_configured` (no provider keys), `reachable`, or `error`.
    Tries Gemini first (simple prose ping, not JSON mode), then Groq if configured.
    """
    settings = get_settings()
    gemini_key = (settings.google_gemini_api_key or "").strip()
    if not gemini_key and not _groq_configured():
        return "not_configured"

    ping = "Reply with the single word: OK"
    if gemini_key:
        try:
            call_gemini(ping, max_tokens=32, expect_json=False)
            return "reachable"
        except LLMError as e:
            logger.warning("LLM health ping (Gemini) failed: %s", e, exc_info=False)

    if _groq_configured():
        try:
            call_groq(ping, max_tokens=32, expect_json=False)
            return "reachable"
        except LLMError as e:
            logger.warning("LLM health ping (Groq) failed: %s", e, exc_info=False)

    return "error"

