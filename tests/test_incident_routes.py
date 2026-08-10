"""HTTP-level tests for protected incident writes."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ops_status_board.app import create_app
from ops_status_board.config import Settings
from ops_status_board.database import get_session
from ops_status_board.models import Base


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Serve the app against an isolated in-memory database."""
    settings = Settings(
        database_url="postgresql+psycopg://app:secret@db/ops_status_board",
        admin_api_token="test-admin-token",
        app_environment="test",
        app_version="test-version",
        _env_file=None,
    )
    application = create_app(settings)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def get_test_session() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    application.dependency_overrides[get_session] = get_test_session
    with TestClient(application) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)
    engine.dispose()


def incident_payload(**overrides: object) -> dict[str, object]:
    """Return a complete, valid incident payload for write-route tests."""
    payload: dict[str, object] = {
        "title": "Public API unavailable",
        "summary": "Requests are returning gateway errors.",
        "severity": "high",
        "status": "investigating",
        "started_at": "2026-08-10T10:00:00Z",
    }
    payload.update(overrides)
    return payload


def create_authorized_incident(client: TestClient) -> int:
    """Create an incident and return its identifier."""
    response = client.post(
        "/api/incidents",
        json=incident_payload(),
        headers={"Authorization": "Bearer test-admin-token"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_write_routes_reject_missing_or_invalid_bearer_token(
    client: TestClient,
) -> None:
    response = client.post("/api/incidents", json=incident_payload())

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Not authenticated"}

    response = client.put(
        "/api/incidents/1",
        json=incident_payload(),
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_authorized_create_and_full_update_incident(client: TestClient) -> None:
    incident_id = create_authorized_incident(client)

    response = client.put(
        f"/api/incidents/{incident_id}",
        json=incident_payload(
            title="Public API restored",
            summary="Error rates returned to normal.",
            severity="medium",
            status="resolved",
            resolved_at="2026-08-10T10:15:00Z",
        ),
        headers={"Authorization": "Bearer test-admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Public API restored"
    assert response.json()["status"] == "resolved"


def test_update_returns_404_for_unknown_incident_after_authentication(
    client: TestClient,
) -> None:
    response = client.put(
        "/api/incidents/404",
        json=incident_payload(),
        headers={"Authorization": "Bearer test-admin-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_invalid_update_is_rejected_before_replacing_incident(
    client: TestClient,
) -> None:
    incident_id = create_authorized_incident(client)

    response = client.put(
        f"/api/incidents/{incident_id}",
        json=incident_payload(status="resolved"),
        headers={"Authorization": "Bearer test-admin-token"},
    )

    assert response.status_code == 422

    unchanged = client.get(f"/api/incidents/{incident_id}")
    assert unchanged.status_code == 200
    assert unchanged.json()["status"] == "investigating"
