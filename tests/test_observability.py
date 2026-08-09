"""Tests for request tracing, safe errors, logging, and redaction."""

import json
from io import StringIO

from fastapi.testclient import TestClient

from ops_status_board.app import create_app
from ops_status_board.config import Settings
from ops_status_board.observability import (
    REDACTED,
    REQUEST_ID_HEADER,
    configure_logging,
    get_request_id,
    redact,
)

DATABASE_SECRET = "postgresql+psycopg://app:database-password@db/ops_status_board"
TOKEN_SECRET = "super-secret-admin-token"


def make_settings(environment: str = "production") -> Settings:
    return Settings(
        database_url=DATABASE_SECRET,
        admin_api_token=TOKEN_SECRET,
        app_environment=environment,
        app_version="test-version",
        _env_file=None,
    )


def make_client(environment: str = "production") -> tuple[TestClient, StringIO]:
    settings = make_settings(environment)
    application = create_app(settings)

    @application.get("/ok")
    async def ok() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/explode")
    async def explode() -> None:
        raise RuntimeError(f"failure used {TOKEN_SECRET} and {DATABASE_SECRET}")

    stream = StringIO()
    configure_logging(settings, stream=stream)
    return TestClient(application, raise_server_exceptions=False), stream


def json_logs(stream: StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_production_completion_log_is_structured_and_omits_query() -> None:
    client, stream = make_client()

    response = client.get("/ok?token=query-secret")
    record = json_logs(stream)[-1]

    assert response.status_code == 200
    assert record["message"] == "request_completed"
    assert record["method"] == "GET"
    assert record["path"] == "/ok"
    assert record["status_code"] == 200
    assert "duration_ms" in record
    assert "query-secret" not in stream.getvalue()


def test_generated_request_id_matches_response_and_log() -> None:
    client, stream = make_client()

    response = client.get("/ok")
    request_id = response.headers[REQUEST_ID_HEADER]

    assert request_id
    assert json_logs(stream)[-1]["request_id"] == request_id


def test_safe_client_request_id_is_reused() -> None:
    client, stream = make_client()

    response = client.get("/ok", headers={REQUEST_ID_HEADER: "client-id_123"})

    assert response.headers[REQUEST_ID_HEADER] == "client-id_123"
    assert json_logs(stream)[-1]["request_id"] == "client-id_123"


def test_unsafe_client_request_id_is_replaced() -> None:
    client, _ = make_client()
    invalid_request_id = "a" * 65

    response = client.get(
        "/ok",
        headers={REQUEST_ID_HEADER: invalid_request_id},
    )

    assert response.headers[REQUEST_ID_HEADER] != invalid_request_id


def test_redaction_hides_sensitive_fields_and_nested_secret_values() -> None:
    safe = redact(
        {
            "route": "/ok",
            "authorization": "Bearer visible-token",
            "nested": {"password": "visible-password"},
        }
    )

    assert safe == {
        "route": "/ok",
        "authorization": REDACTED,
        "nested": {"password": REDACTED},
    }


def test_unexpected_error_is_safe_and_traceable() -> None:
    client, stream = make_client()

    response = client.get("/explode")
    records = json_logs(stream)
    request_id = response.headers[REQUEST_ID_HEADER]

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
        "request_id": request_id,
    }
    assert [record["message"] for record in records] == [
        "unhandled_exception",
        "request_completed",
    ]
    assert all(record["request_id"] == request_id for record in records)
    assert records[-1]["status_code"] == 500
    assert TOKEN_SECRET not in stream.getvalue()
    assert DATABASE_SECRET not in stream.getvalue()
    assert REDACTED in stream.getvalue()


def test_normal_404_is_not_logged_as_unhandled_exception() -> None:
    client, stream = make_client()

    response = client.get("/missing")
    records = json_logs(stream)

    assert response.status_code == 404
    assert [record["message"] for record in records] == ["request_completed"]
    assert records[0]["status_code"] == 404


def test_development_log_is_readable_text() -> None:
    client, stream = make_client("development")

    response = client.get("/ok")

    assert response.status_code == 200
    assert "INFO ops_status_board.http request_completed" in stream.getvalue()
    assert not stream.getvalue().lstrip().startswith("{")


def test_request_context_is_clear_outside_request() -> None:
    client, _ = make_client()

    client.get("/ok")

    assert get_request_id() == "-"


def test_structured_log_extra_secret_is_redacted() -> None:
    settings = make_settings()
    stream = StringIO()
    logger = configure_logging(settings, stream=stream)

    logger.info(
        "authentication_failed",
        extra={"admin_api_token": "another-visible-token", "path": "/write"},
    )

    record = json_logs(stream)[0]
    assert record["admin_api_token"] == REDACTED
    assert record["path"] == "/write"
    assert "another-visible-token" not in stream.getvalue()
