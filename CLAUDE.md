# Project context for Claude Code

## What this project is

A small portfolio demo: a LangGraph-based agentic harness that calibrates a simulated qubit. Built as preparation for a Senior AI Developer (Agentic Systems) interview where the target customer is almost certainly IQM Quantum Computers (Espoo, Finland) and the role involves building a "harness" — a closed-loop control framework that lets AI agents interact with physical quantum hardware safely and deterministically.

The demo is intentionally small but architecturally honest: the same patterns scale to real hardware.

## Architectural principles (do not violate without asking)

1. **The agent never touches hardware directly.** Every hardware-facing call goes through a deterministic harness layer that validates inputs against safety bounds, enforces idempotency where possible, and logs every interaction. The agent proposes, the harness executes.

2. **Typed I/O everywhere.** Use Pydantic v2 models for every tool input and output. No raw dicts crossing module boundaries. This is non-negotiable — it is both good practice and a deliberate signal in interview review.

3. **Deterministic validators, probabilistic agents.** Anything safety-relevant (parameter bounds, rate limits, sanity checks on measurements) is plain Python, not LLM-judged. The LLM decides *what* to try; deterministic code decides *whether it is allowed*.

4. **Observable by default.** Every node in the LangGraph state machine emits structured logs. Langfuse traces are enabled from the first commit, not bolted on later.

5. **Small and finishable over impressive and unfinished.** A working end-to-end loop with five iterations beats a half-built framework. Aim for a runnable demo by the end of day one.

## Stack

- Python 3.11+
- LangGraph (latest stable) for the state machine
- Pydantic v2 for typed models
- Langfuse for tracing
- Anthropic SDK (Claude Sonnet for the agent, configurable)
- pytest for tests
- ruff for linting, mypy for type checking
- uv for dependency management (preferred) or pip+venv as fallback

## Domain model

The simulated qubit has one tunable parameter: pulse amplitude (a float in a bounded range). The "measurement" returns a noisy fidelity score, with a true optimum hidden somewhere in the range. The agent's job is to find the optimum within a budget of measurements.

This is a deliberate simplification of real qubit calibration but preserves the essential loop: propose parameter → validate → measure → analyze → decide next.

## Repository structure (target)

```
qubit-harness/
├── CLAUDE.md                    # this file
├── DECISIONS.md                 # architecture decision log (append-only)
├── README.md                    # user-facing intro + run instructions
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/
│   └── qubit_harness/
│       ├── __init__.py
│       ├── models.py            # Pydantic models for all tool I/O
│       ├── simulator.py         # mock qubit (deterministic seed for tests)
│       ├── harness.py           # safety validation + hardware abstraction
│       ├── tools.py             # LangGraph tool definitions
│       ├── graph.py             # state machine
│       ├── tracing.py           # Langfuse setup
│       └── main.py              # CLI entry point
└── tests/
    ├── test_simulator.py
    ├── test_harness.py
    └── test_graph.py
```

## Working agreements with Claude Code

- **Show structure before writing code.** When starting a new component, propose the file layout and key types first. Wait for confirmation before generating implementation.
- **One concern per commit.** Each git commit should touch one logical unit (simulator, harness, graph, etc.). Suggest commit messages.
- **Update DECISIONS.md on non-obvious choices.** When you pick LangGraph over Pydantic AI, or pydantic v2 over dataclasses, or a specific Langfuse pattern, write a 2–4 sentence entry in DECISIONS.md explaining why.
- **Tests before or alongside implementation for safety-critical code.** The harness validators must have tests. The agent loop can be tested at integration level.
- **Ask before adding dependencies.** No silent additions to pyproject.toml. If a new library would help, propose it with a one-line justification.
- **Comment sparingly, name well.** Production-style code, not tutorial-style code. Comments explain *why*, not *what*.
- **English in code and commits, Finnish acceptable in README user-facing sections.**

## Out of scope (do not build unless asked)

- A web UI
- Multi-agent orchestration
- Real hardware integration (this is a simulator)
- GraphRAG / vector store (mention in README as natural extension, do not implement)
- Authentication, deployment, Docker

## Definition of done for the demo

1. `uv run python -m qubit_harness.main` runs the calibration loop end-to-end
2. Langfuse trace is visible with at least 5 tool calls in one run
3. Tests pass: `pytest`
4. Type check passes: `mypy src/`
5. README explains the architecture in under 300 words with one ASCII diagram
6. DECISIONS.md has at least 3 entries
7. Clean git history with focused commits
