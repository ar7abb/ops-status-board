"""FastAPI application construction."""

from fastapi import FastAPI

from ops_status_board.config import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Validate configuration before returning a ready application object."""
    application_settings = settings if settings is not None else load_settings()
    application = FastAPI(
        title="Ops Status Board",
        version=application_settings.app_version,
    )
    application.state.settings = application_settings
    return application
