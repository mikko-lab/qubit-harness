# Architecture Decision Log

Append-only. Each entry: date, decision, rationale.

---

## 2026-05-24 — Gaussian noise over uniform noise in simulator

Used `random.gauss(0, 0.05)` rather than uniform noise. Gaussian noise more accurately models physical measurement error in qubit readout (photon shot noise, amplifier noise). It also makes naive grid-search slightly harder to distinguish from optimum, which is pedagogically useful.

## 2026-05-24 — `random.Random(seed)` per call rather than module-level RNG

Each `measure()` call constructs its own `random.Random(seed)` instance. This keeps measurements independent and reproducible regardless of call order, which matters for tests and replay. A shared module-level RNG would make test ordering a hidden dependency.

## 2026-05-24 — Hidden optimum not exported from simulator module

`_TRUE_OPTIMUM = 0.73` is module-private. Tests verify statistical behaviour (optimum beats edges by >0.3 average fidelity) rather than asserting the exact value. This prevents tests from accidentally leaking the answer to the agent layer.

