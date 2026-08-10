"""Opt-in integration tests backed by the disposable PostgreSQL database."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from ops_status_board.app import create_app
from ops_status_board.config import Settings, load_settings

TEST_DATABASE_NAME = "ops_status_board_test"

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_INTEGRATION") != "1",
    reason="set RUN_POSTGRES_INTEGRATION=1 to use the disposable PostgreSQL database",
)


def integration_settings() -> Settings:
    """Build test settings that use only the disposable PostgreSQL database."""
    source_settings = load_settings()
    test_url = make_url(source_settings.database_url.get_secret_value()).set(
        database=TEST_DATABASE_NAME,
    )

    return Settings(
        database_url=test_url.render_as_string(hide_password=False),
        admin_api_token=source_settings.admin_api_token.get_secret_value(),
        app_environment="test",
        app_version="integration-test",
        log_level=source_settings.log_level,
        _env_file=None,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Serve the app against a verified, cleaned PostgreSQL test database."""
    settings = integration_settings()
    cleanup_engine = create_engine(settings.database_url.get_secret_value())
    verified_test_database = False

    try:
        with cleanup_engine.connect() as connection:
            database_name = connection.scalar(text("SELECT current_database()"))

        if database_name != TEST_DATABASE_NAME:
            raise RuntimeError(
                "refusing to run integration tests outside test database"
            )

        verified_test_database = True
        with cleanup_engine.begin() as connection:
            connection.execute(text("DELETE FROM incidents"))

        application = create_app(settings)
        with TestClient(application) as test_client:
            yield test_client
    finally:
        if verified_test_database:
            with cleanup_engine.begin() as connection:
                connection.execute(text("DELETE FROM incidents"))
        cleanup_engine.dispose()


def admin_headers() -> dict[str, str]:
    """Build an authenticated header without printing the private token."""
    token = load_settings().admin_api_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


def test_postgres_persists_an_incident_created_through_the_api(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/incidents",
        json={
            "title": "PostgreSQL integration check",
            "summary": "The incident must persist in the disposable test database.",
            "severity": "high",
            "started_at": "2026-08-10T10:00:00Z",
        },
        headers=admin_headers(),
    )

    assert response.status_code == 201
    incident_id = response.json()["id"]

    listed = client.get("/api/incidents")

    assert listed.status_code == 200
    assert [incident["id"] for incident in listed.json()] == [incident_id]


def test_postgres_test_database_has_current_migration() -> None:
    settings = integration_settings()
    engine = create_engine(settings.database_url.get_secret_value())

    try:
        with engine.connect() as connection:
            database_name = connection.scalar(text("SELECT current_database()"))
            revision = connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )
            incidents_table_exists = connection.scalar(
                text("SELECT to_regclass('public.incidents') IS NOT NULL")
            )
    finally:
        engine.dispose()

    assert database_name == TEST_DATABASE_NAME
    assert revision == "3b07435d5c68"
    assert incidents_table_exists is True
