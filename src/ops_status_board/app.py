"""FastAPI application construction."""

from fastapi import FastAPI

from ops_status_board.config import Settings, load_settings
from ops_status_board.database import install_database
from ops_status_board.observability import install_observability
from ops_status_board.routes import api_router, dashboard_router, operations_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Validate configuration before returning a ready application object."""
    application_settings = settings if settings is not None else load_settings()
    application = FastAPI(
        title="Ops Status Board",
        version=application_settings.app_version,
    )
    application.state.settings = application_settings
    install_database(application, application_settings)
    install_observability(application, application_settings)
    application.include_router(api_router)
    application.include_router(dashboard_router)
    application.include_router(operations_router)
    return application
