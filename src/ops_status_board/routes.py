"""Incident API routes."""

from pathlib import Path
from secrets import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ops_status_board.database import get_session
from ops_status_board.models import Incident
from ops_status_board.schemas import IncidentCreate, IncidentResponse

api_router = APIRouter(prefix="/api/incidents", tags=["incidents"])

dashboard_router = APIRouter(tags=["dashboard"])
operations_router = APIRouter(tags=["operations"])

templates = Jinja2Templates(
    directory=str(Path(__file__).parent / "templates"),
)

bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[Session, Depends(get_session)]
AdminCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def require_admin(request: Request, credentials: AdminCredentials) -> None:
    """Require the configured bearer token without exposing it."""
    expected_token = request.app.state.settings.admin_api_token.get_secret_value()
    supplied_token = credentials.credentials if credentials is not None else ""

    if not compare_digest(supplied_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


@api_router.get("", response_model=list[IncidentResponse])
def list_incidents(session: DatabaseSession) -> list[Incident]:
    """Return incidents with the most recently started first."""
    statement = select(Incident).order_by(Incident.started_at.desc())
    return list(session.scalars(statement))


@api_router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, session: DatabaseSession) -> Incident:
    """Return one incident or a normal 404 response."""
    incident = session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return incident


@api_router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_incident(payload: IncidentCreate, session: DatabaseSession) -> Incident:
    """Create one authenticated incident."""
    incident = Incident(**payload.model_dump())
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


@api_router.put(
    "/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[Depends(require_admin)],
)
def update_incident(
    incident_id: int,
    payload: IncidentCreate,
    session: DatabaseSession,
) -> Incident:
    """Replace one authenticated incident or return a normal 404 response."""
    incident = session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for field, value in payload.model_dump().items():
        setattr(incident, field, value)
    session.commit()
    session.refresh(incident)
    return incident


@operations_router.get("/health/live")
def liveness() -> dict[str, str]:
    """Confirm that the HTTP application process is running."""
    return {"status": "ok"}


@operations_router.get("/health/ready")
def readiness(session: DatabaseSession) -> dict[str, str]:
    """Confirm that the application can complete a minimal database query."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Not ready",
        ) from None
    return {"status": "ok"}


@operations_router.get("/version")
def version(request: Request) -> dict[str, str]:
    """Return the configured application version for diagnostics."""
    return {"version": request.app.state.settings.app_version}


@operations_router.get(
    "/metrics",
    dependencies=[Depends(require_admin)],
)
def metrics() -> Response:
    """Return the protected Prometheus metrics payload."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@dashboard_router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: DatabaseSession) -> Response:
    """Render the current incidents as completed HTML."""
    statement = select(Incident).order_by(Incident.started_at.desc())
    incidents = list(session.scalars(statement))
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"incidents": incidents},
    )
