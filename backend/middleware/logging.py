"""Structured JSON request logging (PRD Section 17)."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from middleware.auth import try_get_user_id_from_authorization

logger = logging.getLogger("job_assistant.api")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_LOG_FILE = _BACKEND_DIR / "logs" / "app.log"


def _ensure_log_file() -> None:
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def _emit(event: str, payload: dict) -> None:
    line = json.dumps(payload, default=str)
    logger.info(line)
    try:
        _ensure_log_file()
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        logger.exception("Failed to append structured log to %s", _LOG_FILE)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one JSON line per completed request (method, path, user_id, duration, status)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        auth_header = request.headers.get("authorization")
        user_id = try_get_user_id_from_authorization(auth_header)
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        incoming = {
            "timestamp": ts,
            "level": "INFO",
            "module": "api",
            "event": "request_received",
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id,
        }
        _emit("request_received", incoming)

        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        complete = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": "INFO",
            "module": "api",
            "event": "request_complete",
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
        _emit("request_complete", complete)
        return response
