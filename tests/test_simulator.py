"""Tests for the qubit simulator."""

import pytest
from qubit_harness.simulator import measure


def test_deterministic_with_same_seed() -> None:
    result_a = measure(0.5, seed=42)
    result_b = measure(0.5, seed=42)
    assert result_a == result_b


def test_different_seeds_produce_different_results() -> None:
    result_a = measure(0.5, seed=1)
    result_b = measure(0.5, seed=2)
    assert result_a != result_b


def test_result_in_valid_range() -> None:
    for seed in range(50):
        result = measure(0.5, seed=seed)
        assert 0.0 <= result <= 1.0


def test_optimum_clearly_outperforms_edges() -> None:
    n = 100
    avg_optimum = sum(measure(0.73, seed=s) for s in range(n)) / n
    avg_low = sum(measure(0.0, seed=s) for s in range(n)) / n
    avg_high = sum(measure(1.0, seed=s) for s in range(n)) / n

    assert avg_optimum > avg_low + 0.3, f"optimum {avg_optimum:.3f} not >> low {avg_low:.3f}"
    assert avg_optimum > avg_high + 0.3, f"optimum {avg_optimum:.3f} not >> high {avg_high:.3f}"


def test_rejects_out_of_bounds_amplitude() -> None:
    with pytest.raises(ValueError):
        measure(-0.01)
    with pytest.raises(ValueError):
        measure(1.01)


def test_boundary_amplitudes_accepted() -> None:
    measure(0.0)
    measure(1.0)
