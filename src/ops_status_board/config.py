"""Typed application configuration loaded from the environment."""

from typing import Literal

from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Validated configuration required to construct the application."""

    database_url: SecretStr
    admin_api_token: SecretStr
    app_version: str
    app_environment: Environment
    log_level: LogLevel = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @field_validator("database_url", "admin_api_token")
    @classmethod
    def secret_must_not_be_empty(cls, value: SecretStr) -> SecretStr:
        """Reject empty required secrets without exposing their values."""
        if not value.get_secret_value().strip():
            raise ValueError("must not be empty")
        return value


class SettingsError(RuntimeError):
    """Safe startup error for missing or invalid application settings."""


def load_settings() -> Settings:
    """Load settings or raise a value-redacted startup error."""
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as error:
        problems = []
        for problem in error.errors(include_input=False):
            field = ".".join(str(part) for part in problem["loc"]).upper()
            problems.append(f"{field}: {problem['msg']}")
        details = "; ".join(problems)
        raise SettingsError(f"Invalid application settings: {details}") from None
