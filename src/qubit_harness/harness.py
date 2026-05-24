"""Deterministic safety harness — validates all requests before touching the simulator."""

import time

from qubit_harness.models import (
    CalibrationState,
    MeasurementRequest,
    MeasurementResult,
    SafetyViolation,
)
from qubit_harness.simulator import measure

_RATE_LIMIT_SECONDS = 0.1
_SESSION_BUDGET = 20


class SafetyViolationError(Exception):
    def __init__(self, violation: SafetyViolation) -> None:
        super().__init__(violation.message)
        self.violation = violation


class CalibrationHarness:
    """Wraps the simulator with deterministic safety checks.

    The agent proposes; this layer decides whether the proposal is allowed.
    No LLM judgement here — only plain Python invariants.
    """

    def __init__(self, session_budget: int = _SESSION_BUDGET) -> None:
        self._budget = session_budget
        self._used = 0
        self._last_measurement_time: float | None = None
        self._history: list[MeasurementResult] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def measure(self, request: MeasurementRequest, seed: int | None = None) -> MeasurementResult:
        """Validate request, run simulator, return result.

        Raises:
            SafetyViolationError: If any safety check fails.
        """
        self._check_budget()
        self._check_rate_limit()
        # Amplitude bounds are already enforced by MeasurementRequest's Field(ge=0, le=1),
        # but an explicit check produces a structured SafetyViolation for callers.
        self._check_amplitude(request.amplitude)

        self._last_measurement_time = time.monotonic()
        self._used += 1

        fidelity = measure(request.amplitude, seed=seed)
        result = MeasurementResult(amplitude=request.amplitude, fidelity=fidelity)
        self._history.append(result)
        return result

    def state(self) -> CalibrationState:
        best = max(self._history, key=lambda r: r.fidelity) if self._history else None
        return CalibrationState(
            history=list(self._history),
            budget_remaining=self._budget - self._used,
            best_so_far=best,
        )

    # ------------------------------------------------------------------
    # Validators — all deterministic, no LLM
    # ------------------------------------------------------------------

    def _check_budget(self) -> None:
        if self._used >= self._budget:
            raise SafetyViolationError(
                SafetyViolation(
                    parameter="budget",
                    value=float(self._used),
                    bound=float(self._budget),
                    message=f"Session budget exhausted ({self._used}/{self._budget} measurements used)",
                )
            )

    def _check_rate_limit(self) -> None:
        if self._last_measurement_time is None:
            return
        elapsed = time.monotonic() - self._last_measurement_time
        if elapsed < _RATE_LIMIT_SECONDS:
            raise SafetyViolationError(
                SafetyViolation(
                    parameter="rate",
                    value=elapsed,
                    bound=_RATE_LIMIT_SECONDS,
                    message=f"Rate limit: {elapsed*1000:.1f}ms since last measurement, minimum {_RATE_LIMIT_SECONDS*1000:.0f}ms required",
                )
            )

    def _check_amplitude(self, amplitude: float) -> None:
        if not (0.0 <= amplitude <= 1.0):
            raise SafetyViolationError(
                SafetyViolation(
                    parameter="amplitude",
                    value=amplitude,
                    bound=1.0,
                    message=f"Amplitude {amplitude} outside allowed range [0.0, 1.0]",
                )
            )
