"""Tests for the FastAPI application factory."""

from pathlib import Path

import pytest
from fastapi import FastAPI

from ops_status_board.app import create_app
from ops_status_board.config import Settings, SettingsError


def test_factory_builds_application_from_injected_settings() -> None:
    settings = Settings(
        database_url="postgresql://app:secret@db/ops_status_board",
        admin_api_token="test-admin-token",
        app_environment="test",
        app_version="test-version",
        _env_file=None,
    )

    application = create_app(settings)

    assert isinstance(application, FastAPI)
    assert application.title == "Ops Status Board"
    assert application.version == "test-version"
    assert application.state.settings is settings


def test_factory_refuses_to_build_without_required_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SettingsError):
        create_app()
