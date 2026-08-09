"""Safe request tracing and application logging."""

import json
import logging
import re
from collections.abc import Mapping, Sequence
from contextvars import ContextVar
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import SecretStr
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from ops_status_board.config import Settings

REQUEST_ID_HEADER = "X-Request-ID"
REDACTED = "[REDACTED]"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SENSITIVE_KEY_PARTS = (
    "authorization",
    "cookie",
    "database_url",
    "password",
    "passwd",
    "private_key",
    "secret",
    "token",
    "api_key",
    "access_key",
)
STANDARD_LOG_RECORD_FIELDS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime"}

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Return the ID associated with the current request context."""
    return _request_id.get()


def select_request_id(candidate: str | None) -> str:
    """Reuse a safe client ID, otherwise generate an opaque UUID."""
    if candidate is not None and REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid4())


def _is_sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower())
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact(value: Any, known_secrets: Sequence[str] = ()) -> Any:
    """Return a log-safe copy without exposing secret fields or known values."""
    if isinstance(value, SecretStr):
        return REDACTED
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED
            if _is_sensitive_key(key)
            else redact(item, known_secrets)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item, known_secrets) for item in value]
    if isinstance(value, str):
        sanitized = value
        for secret in known_secrets:
            if secret:
                sanitized = sanitized.replace(secret, REDACTED)
        return sanitized
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


class SafeFormatter(logging.Formatter):
    """Render redacted logs as JSON in production and text elsewhere."""

    def __init__(self, *, use_json: bool, known_secrets: Sequence[str]) -> None:
        super().__init__()
        self.use_json = use_json
        self.known_secrets = tuple(known_secrets)

    def format(self, record: logging.LogRecord) -> str:
        fields: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", get_request_id()),
        }
        for key, value in record.__dict__.items():
            if key not in STANDARD_LOG_RECORD_FIELDS and key not in fields:
                fields[key] = value
        if record.exc_info:
            fields["exception"] = self.formatException(record.exc_info)
        safe_fields = redact(fields, self.known_secrets)
        if self.use_json:
            return json.dumps(safe_fields, sort_keys=True)
        extras = " ".join(
            f"{key}={value}"
            for key, value in safe_fields.items()
            if key not in {"timestamp", "level", "logger", "message"}
        )
        suffix = f" {extras}" if extras else ""
        return (
            f"{safe_fields['timestamp']} {safe_fields['level']} "
            f"{safe_fields['logger']} {safe_fields['message']}{suffix}"
        )


def configure_logging(
    settings: Settings,
    *,
    stream: Any | None = None,
) -> logging.Logger:
    """Configure the application logger without changing unrelated loggers."""
    logger = logging.getLogger("ops_status_board")
    logger.handlers.clear()
    logger.setLevel(settings.log_level)
    logger.propagate = False

    handler = logging.StreamHandler(stream)
    handler.setLevel(settings.log_level)
    handler.setFormatter(
        SafeFormatter(
            use_json=settings.app_environment == "production",
            known_secrets=(
                settings.database_url.get_secret_value(),
                settings.admin_api_token.get_secret_value(),
            ),
        )
    )
    logger.addHandler(handler)
    return logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Trace requests and convert unexpected failures into safe responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = select_request_id(request.headers.get(REQUEST_ID_HEADER))
        context_token = _request_id.set(request_id)
        started = perf_counter()
        logger = logging.getLogger("ops_status_board.http")
        try:
            try:
                response = await call_next(request)
            except Exception as error:
                logger.exception(
                    "unhandled_exception",
                    extra={"exception_type": type(error).__name__},
                )
                response = JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "request_id": request_id,
                    },
                )

            response.headers[REQUEST_ID_HEADER] = request_id
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                },
            )
            return response
        finally:
            _request_id.reset(context_token)


def install_observability(application: FastAPI, settings: Settings) -> None:
    """Install logging and request middleware on an application."""
    configure_logging(settings)
    application.add_middleware(RequestContextMiddleware)
