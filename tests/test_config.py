"""Tests for validated and secret-safe application configuration."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from ops_status_board.config import Settings, SettingsError, load_settings

DATABASE_URL = "postgresql://app:database-secret@db/ops_status_board"
ADMIN_API_TOKEN = "test-admin-token"
SETTING_NAMES = (
    "DATABASE_URL",
    "ADMIN_API_TOKEN",
    "APP_VERSION",
    "APP_ENVIRONMENT",
    "LOG_LEVEL",
)


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": DATABASE_URL,
        "admin_api_token": ADMIN_API_TOKEN,
        "app_version": "test-version",
        "app_environment": "test",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def clear_application_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in SETTING_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_settings_require_identity_and_have_safe_log_default() -> None:
    settings = make_settings()

    assert settings.app_environment == "test"
    assert settings.app_version == "test-version"
    assert settings.log_level == "INFO"


def test_secret_values_are_redacted_from_settings_representation() -> None:
    settings = make_settings()

    representation = repr(settings)
    assert "database-secret" not in representation
    assert ADMIN_API_TOKEN not in representation
    assert "**********" in representation


def test_invalid_environment_is_rejected_without_echoing_input() -> None:
    invalid_environment = "private-invalid-environment"

    with pytest.raises(ValidationError) as captured:
        make_settings(app_environment=invalid_environment)

    assert invalid_environment not in str(captured.value)


def test_load_settings_reports_missing_fields_safely(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_application_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SettingsError) as captured:
        load_settings()

    message = str(captured.value)
    assert "DATABASE_URL" in message
    assert "ADMIN_API_TOKEN" in message
    assert "APP_VERSION" in message
    assert "APP_ENVIRONMENT" in message
    assert "postgresql://" not in message
    assert "test-admin-token" not in message


def test_load_settings_rejects_legacy_dotenv_names(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_application_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "\n".join(
            (
                f"DATABASE_URL={DATABASE_URL}",
                f"ADMIN_API_TOKEN={ADMIN_API_TOKEN}",
                "APP_VERSION=test-version",
                "APP_ENVIRONMENT=test",
                "APP_ENV=production",
                "WRITE_API_TOKEN=legacy-test-token",
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(SettingsError) as captured:
        load_settings()

    message = str(captured.value)
    assert "APP_ENV" in message
    assert "WRITE_API_TOKEN" in message
    assert "production" not in message
    assert "legacy-test-token" not in message


def test_load_settings_reads_approved_environment_names(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_application_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("ADMIN_API_TOKEN", ADMIN_API_TOKEN)
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("APP_VERSION", "test-version")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    settings = load_settings()

    assert settings.database_url.get_secret_value() == DATABASE_URL
    assert settings.admin_api_token.get_secret_value() == ADMIN_API_TOKEN
    assert settings.app_environment == "test"
    assert settings.app_version == "test-version"
    assert settings.log_level == "WARNING"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("database_url", "   "),
        ("admin_api_token", ""),
    ],
)
def test_settings_reject_blank_secret_values(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match="must not be empty"):
        make_settings(**{field: value})
