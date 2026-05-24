"""Tool wrappers — thin boundary between agent and harness."""

from qubit_harness.harness import CalibrationHarness
from qubit_harness.models import MeasurementRequest, MeasurementResult


def run_measurement(
    harness: CalibrationHarness,
    amplitude: float,
    reason: str | None = None,
    seed: int | None = None,
) -> MeasurementResult:
    """Execute a single measurement through the safety harness."""
    request = MeasurementRequest(amplitude=amplitude, reason=reason)
    return harness.measure(request, seed=seed)
