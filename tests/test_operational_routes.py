"""HTTP-level tests for dashboard and operational routes."""

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from ops_status_board.app import create_app
from ops_status_board.config import Settings
from ops_status_board.database import get_session


class ReadySession:
    """Minimal session double for dashboard and readiness checks."""

    def __init__(self) -> None:
        self.executed = False

    def execute(self, statement: object) -> None:
        self.executed = True

    def scalars(self, statement: object) -> list[object]:
        return []


class UnavailableSession(ReadySession):
    """Session double that simulates a failed readiness query."""

    def execute(self, statement: object) -> None:
        raise SQLAlchemyError("database unavailable")


def build_client(session: ReadySession) -> TestClient:
    """Build an application whose database dependency yields the supplied double."""
    settings = Settings(
        database_url="postgresql+psycopg://app:secret@db/ops_status_board",
        admin_api_token="test-admin-token",
        app_environment="test",
        app_version="test-version",
        _env_file=None,
    )
    application = create_app(settings)

    def get_test_session() -> Generator[ReadySession, None, None]:
        yield session

    application.dependency_overrides[get_session] = get_test_session
    return TestClient(application)


def test_dashboard_renders_an_accessible_empty_state() -> None:
    with build_client(ReadySession()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "No incidents have been recorded." in response.text


def test_liveness_and_version_do_not_require_database_access() -> None:
    unavailable_session = UnavailableSession()
    with build_client(unavailable_session) as client:
        liveness = client.get("/health/live")
        version = client.get("/version")

    assert liveness.json() == {"status": "ok"}
    assert version.json() == {"version": "test-version"}
    assert unavailable_session.executed is False


def test_readiness_reports_database_availability_without_leaking_error() -> None:
    ready_session = ReadySession()
    with build_client(ready_session) as client:
        healthy = client.get("/health/ready")

    assert healthy.json() == {"status": "ok"}
    assert ready_session.executed is True

    with build_client(UnavailableSession()) as client:
        unavailable = client.get("/health/ready")

    assert unavailable.status_code == 503
    assert unavailable.json() == {"detail": "Not ready"}
    assert "database unavailable" not in unavailable.text


def test_metrics_requires_bearer_token_and_returns_prometheus_text() -> None:
    with build_client(ReadySession()) as client:
        denied = client.get("/metrics")
        allowed = client.get(
            "/metrics",
            headers={"Authorization": "Bearer test-admin-token"},
        )

    assert denied.status_code == 401
    assert denied.headers["www-authenticate"] == "Bearer"
    assert allowed.status_code == 200
    assert allowed.headers["content-type"].startswith("text/plain")
    assert "ops_status_board_info 1" in allowed.text
