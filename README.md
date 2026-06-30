# qubit-harness

[![CI](https://github.com/mikko-lab/qubit-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/mikko-lab/qubit-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A LangGraph-based agentic harness that calibrates a simulated qubit. Built as a portfolio demo for agentic systems work — the same closed-loop pattern applies to real hardware.

## Architecture

The agent proposes; the harness decides whether the proposal is safe to execute.

```
┌─────────────────────────────────────────────┐
│                 LangGraph loop              │
│                                             │
│  ┌──────────────┐     ┌──────────────────┐  │
│  │   propose    │────▶│    execute       │  │
│  │  (Claude)    │     │  (harness)       │  │
│  └──────────────┘     └────────┬─────────┘  │
│          ▲                     │             │
│          │            ┌────────▼─────────┐  │
│          │            │    analyze       │  │
│     loop │            │  (update best)   │  │
│          │            └────────┬─────────┘  │
│          │                     │             │
│          │            ┌────────▼─────────┐  │
│          └────────────│   decide_next    │  │
│                       │  budget? done?   │──▶ END
│                       └──────────────────┘  │
└─────────────────────────────────────────────┘

  Harness layer (deterministic):
    • amplitude bounds [0.0, 1.0]
    • rate limit 100 ms between calls
    • session budget (default 15)
```

The harness layer is plain Python — no LLM judgement on safety checks. Langfuse traces every LLM call and tool invocation.

## Install

```bash
git clone https://github.com/mikko-lab/qubit-harness
cd qubit-harness
uv sync
cp .env.example .env   # add ANTHROPIC_API_KEY
```

## Run

```bash
uv run python -m qubit_harness.main
uv run python -m qubit_harness.main --budget 10 --no-trace
uv run python -m qubit_harness.main --budget 5 --seed 42
```

Example output:

```
Starting calibration  budget=5  trace=off

── Calibration complete ──────────────────────────────
  Best amplitude   : 0.7500
  Best fidelity    : 1.0000
  Measurements used: 3
  Budget remaining : 2
──────────────────────────────────────────────────────
```

## Tests

```bash
uv run pytest
uv run mypy src/
uv run ruff check src/
```

## Natural extensions

**GraphRAG** — store measurement history in a graph database; let the agent query similar past calibrations across qubit instances.

**MCP server** — expose the harness as an MCP tool so any MCP-compatible agent can drive calibration without custom integration code.
