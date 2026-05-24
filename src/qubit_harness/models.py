"""Typed I/O models for all tool boundaries."""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class MeasurementRequest(BaseModel):
    amplitude: float = Field(..., ge=0.0, le=1.0, description="Pulse amplitude to measure")
    reason: str | None = Field(None, description="Agent's rationale for this choice")


class MeasurementResult(BaseModel):
    measurement_id: str = Field(default_factory=lambda: str(uuid4()))
    amplitude: float = Field(..., ge=0.0, le=1.0)
    fidelity: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CalibrationState(BaseModel):
    history: list[MeasurementResult] = Field(default_factory=list)
    budget_remaining: int = Field(..., ge=0)
    best_so_far: MeasurementResult | None = None

    @model_validator(mode="after")
    def best_consistent_with_history(self) -> "CalibrationState":
        if self.best_so_far is not None and not self.history:
            raise ValueError("best_so_far set but history is empty")
        return self


class SafetyViolation(BaseModel):
    parameter: str
    value: float
    bound: float
    message: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v
