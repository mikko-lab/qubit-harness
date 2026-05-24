"""Mock qubit simulator with a hidden optimal pulse amplitude."""

import math
import random

_TRUE_OPTIMUM = 0.73
_NOISE_SIGMA = 0.05
_AMPLITUDE_MIN = 0.0
_AMPLITUDE_MAX = 1.0


def _fidelity(amplitude: float) -> float:
    """Noiseless fidelity: gaussian peak centred at the true optimum."""
    return math.exp(-((amplitude - _TRUE_OPTIMUM) ** 2) / (2 * 0.15**2))


def measure(amplitude: float, seed: int | None = None) -> float:
    """Return a noisy fidelity measurement for the given pulse amplitude.

    Args:
        amplitude: Pulse amplitude in [0.0, 1.0].
        seed: RNG seed for reproducible measurements.

    Returns:
        Fidelity in [0.0, 1.0], clipped after adding Gaussian noise.

    Raises:
        ValueError: If amplitude is outside [0.0, 1.0].
    """
    if not (_AMPLITUDE_MIN <= amplitude <= _AMPLITUDE_MAX):
        raise ValueError(
            f"amplitude {amplitude} outside [{_AMPLITUDE_MIN}, {_AMPLITUDE_MAX}]"
        )

    rng = random.Random(seed)
    noise = rng.gauss(0.0, _NOISE_SIGMA)
    return float(max(0.0, min(1.0, _fidelity(amplitude) + noise)))
