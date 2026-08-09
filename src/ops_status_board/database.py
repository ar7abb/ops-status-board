"""Database engine and session lifecycle helpers."""

from collections.abc import Generator
from typing import cast

from fastapi import FastAPI, Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ops_status_board.config import Settings

DatabaseSessionFactory = sessionmaker[Session]


def install_database(application: FastAPI, settings: Settings) -> None:
    """Attach a lazy database engine and session factory to the application."""
    engine: Engine = create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
    )
    application.state.database_engine = engine
    application.state.database_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    application.router.on_shutdown.append(engine.dispose)


def get_session(request: Request) -> Generator[Session, None, None]:
    """Provide one session per request, rolling back failed work safely."""
    session_factory = cast(
        DatabaseSessionFactory,
        request.app.state.database_session_factory,
    )
    session = session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
