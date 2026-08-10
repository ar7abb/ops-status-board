"""Validated API data contracts for incidents."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

IncidentSeverity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["investigating", "identified", "monitoring", "resolved"]


class IncidentCreate(BaseModel):
    """Validated data accepted when an operator creates an incident."""

    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1)
    severity: IncidentSeverity
    status: IncidentStatus = "investigating"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None

    @model_validator(mode="after")
    def resolved_timestamp_matches_status(self) -> "IncidentCreate":
        """Keep resolved status and timestamp consistent."""
        if self.status == "resolved" and self.resolved_at is None:
            raise ValueError("resolved incidents require resolved_at")
        if self.status != "resolved" and self.resolved_at is not None:
            raise ValueError("only resolved incidents may include resolved_at")
        return self


class IncidentResponse(IncidentCreate):
    """Incident data returned by the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
