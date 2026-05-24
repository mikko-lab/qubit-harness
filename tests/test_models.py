"""Tests for Pydantic I/O models."""

import pytest
from pydantic import ValidationError

from qubit_harness.models import (
    CalibrationState,
    MeasurementRequest,
    MeasurementResult,
    SafetyViolation,
)


# --- MeasurementRequest ---

def test_request_valid() -> None:
    r = MeasurementRequest(amplitude=0.5)
    assert r.amplitude == 0.5
    assert r.reason is None


def test_request_amplitude_below_zero() -> None:
    with pytest.raises(ValidationError):
        MeasurementRequest(amplitude=-0.01)


def test_request_amplitude_above_one() -> None:
    with pytest.raises(ValidationError):
        MeasurementRequest(amplitude=1.01)


def test_request_with_reason() -> None:
    r = MeasurementRequest(amplitude=0.3, reason="exploring lower range")
    assert r.reason == "exploring lower range"


# --- MeasurementResult ---

def test_result_has_generated_id_and_timestamp() -> None:
    r = MeasurementResult(amplitude=0.5, fidelity=0.8)
    assert r.measurement_id
    assert r.timestamp is not None


def test_result_fidelity_out_of_range() -> None:
    with pytest.raises(ValidationError):
        MeasurementResult(amplitude=0.5, fidelity=1.1)

    with pytest.raises(ValidationError):
        MeasurementResult(amplitude=0.5, fidelity=-0.1)


def test_result_amplitude_out_of_range() -> None:
    with pytest.raises(ValidationError):
        MeasurementResult(amplitude=1.5, fidelity=0.5)


# --- CalibrationState ---

def test_state_empty_initial() -> None:
    s = CalibrationState(budget_remaining=10)
    assert s.history == []
    assert s.best_so_far is None


def test_state_negative_budget() -> None:
    with pytest.raises(ValidationError):
        CalibrationState(budget_remaining=-1)


def test_state_best_without_history_invalid() -> None:
    result = MeasurementResult(amplitude=0.5, fidelity=0.8)
    with pytest.raises(ValidationError):
        CalibrationState(budget_remaining=5, best_so_far=result, history=[])


def test_state_best_consistent_with_history() -> None:
    result = MeasurementResult(amplitude=0.5, fidelity=0.8)
    s = CalibrationState(budget_remaining=5, history=[result], best_so_far=result)
    assert s.best_so_far == result


# --- SafetyViolation ---

def test_violation_valid() -> None:
    v = SafetyViolation(parameter="amplitude", value=1.5, bound=1.0, message="exceeds max")
    assert v.parameter == "amplitude"


def test_violation_empty_message() -> None:
    with pytest.raises(ValidationError):
        SafetyViolation(parameter="amplitude", value=1.5, bound=1.0, message="  ")
