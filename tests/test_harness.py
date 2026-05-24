"""Tests for CalibrationHarness — safety-critical, so coverage must be thorough."""

import time

import pytest
from pydantic import ValidationError

from qubit_harness.harness import CalibrationHarness, SafetyViolationError
from qubit_harness.models import MeasurementRequest


def _req(amplitude: float, reason: str | None = None) -> MeasurementRequest:
    return MeasurementRequest(amplitude=amplitude, reason=reason)


# --- Happy path ---

def test_valid_measurement_returns_result() -> None:
    harness = CalibrationHarness()
    result = harness.measure(_req(0.5), seed=0)
    assert 0.0 <= result.fidelity <= 1.0
    assert result.amplitude == 0.5
    assert result.measurement_id


def test_state_reflects_measurement() -> None:
    harness = CalibrationHarness()
    harness.measure(_req(0.5), seed=0)
    state = harness.state()
    assert len(state.history) == 1
    assert state.budget_remaining == 19
    assert state.best_so_far is not None


def test_best_so_far_tracks_highest_fidelity() -> None:
    harness = CalibrationHarness()
    time.sleep(0.11)
    harness.measure(_req(0.1), seed=0)
    time.sleep(0.11)
    harness.measure(_req(0.73), seed=0)  # near optimum — should be best
    state = harness.state()
    assert state.best_so_far is not None
    assert state.best_so_far.amplitude == pytest.approx(0.73)


# --- Budget exhaustion ---

def test_budget_exhausted_raises_safety_violation() -> None:
    harness = CalibrationHarness(session_budget=2)
    harness.measure(_req(0.5), seed=0)
    time.sleep(0.11)
    harness.measure(_req(0.6), seed=1)
    time.sleep(0.11)
    with pytest.raises(SafetyViolationError) as exc_info:
        harness.measure(_req(0.7), seed=2)
    assert exc_info.value.violation.parameter == "budget"


def test_budget_of_one_allows_exactly_one_measurement() -> None:
    harness = CalibrationHarness(session_budget=1)
    harness.measure(_req(0.5), seed=0)
    time.sleep(0.11)
    with pytest.raises(SafetyViolationError):
        harness.measure(_req(0.6), seed=1)


# --- Rate limit ---

def test_rate_limit_blocks_rapid_successive_calls() -> None:
    harness = CalibrationHarness()
    harness.measure(_req(0.5), seed=0)
    with pytest.raises(SafetyViolationError) as exc_info:
        harness.measure(_req(0.6), seed=1)
    assert exc_info.value.violation.parameter == "rate"


def test_rate_limit_passes_after_sufficient_delay() -> None:
    harness = CalibrationHarness()
    harness.measure(_req(0.5), seed=0)
    time.sleep(0.11)
    result = harness.measure(_req(0.6), seed=1)
    assert result.fidelity >= 0.0


def test_first_measurement_not_rate_limited() -> None:
    harness = CalibrationHarness()
    result = harness.measure(_req(0.5), seed=0)
    assert result is not None


# --- Amplitude bounds ---

def test_pydantic_rejects_out_of_bounds_before_harness() -> None:
    with pytest.raises(ValidationError):
        MeasurementRequest(amplitude=1.5)


# --- Violation structure ---

def test_safety_violation_error_carries_structured_violation() -> None:
    harness = CalibrationHarness(session_budget=0)
    with pytest.raises(SafetyViolationError) as exc_info:
        harness.measure(_req(0.5))
    v = exc_info.value.violation
    assert v.parameter == "budget"
    assert v.bound == 0.0
    assert v.message
