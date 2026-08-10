"""Tests for validated incident API data."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ops_status_board.schemas import IncidentCreate


def test_incident_defaults_to_investigating_with_utc_start_time() -> None:
    incident = IncidentCreate(
        title="API unavailable",
        summary="The public API is not responding.",
        severity="high",
    )

    assert incident.status == "investigating"
    assert incident.started_at.tzinfo is not None
    assert incident.resolved_at is None


def test_unknown_severity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        IncidentCreate(
            title="Invalid severity",
            summary="This input must be rejected.",
            severity="urgent",
        )


def test_resolved_incident_requires_resolved_timestamp() -> None:
    with pytest.raises(ValidationError, match="resolved incidents require resolved_at"):
        IncidentCreate(
            title="Resolved without time",
            summary="This state is inconsistent.",
            severity="low",
            status="resolved",
        )


def test_active_incident_rejects_resolved_timestamp() -> None:
    with pytest.raises(
        ValidationError,
        match="only resolved incidents may include resolved_at",
    ):
        IncidentCreate(
            title="Active with resolved time",
            summary="This state is inconsistent.",
            severity="medium",
            resolved_at=datetime.now(UTC),
        )
