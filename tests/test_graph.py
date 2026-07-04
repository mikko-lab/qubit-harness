"""Integration tests for the LangGraph calibration loop."""

import time
import uuid
from unittest.mock import patch

from langchain_core.messages import AIMessage

from qubit_harness.graph import AgentState, build_graph
from qubit_harness.harness import CalibrationHarness


class _ScriptedLLM:
    """Deterministic stand-in for ChatAnthropic.

    Proposes a fixed amplitude sequence regardless of measurement history,
    then converges. This isolates the test to the seed -> noise wiring: any
    variance in the resulting history can only come from the harness/simulator.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._call_count = 0

    def invoke(self, messages: list[object]) -> AIMessage:
        time.sleep(0.11)  # stay clear of the harness's 0.1s rate limit
        self._call_count += 1
        n = self._call_count
        if n > 3:
            return AIMessage(content="CONVERGED: 0.7")
        amplitude = 0.1 + 0.2 * (n - 1)
        return AIMessage(content=f"Trying amplitude {amplitude:.2f} as step {n}.")


def _run_once(seed: int) -> list:  # type: ignore[type-arg]
    harness = CalibrationHarness(session_budget=10)
    with patch("qubit_harness.graph.ChatAnthropic", _ScriptedLLM):
        graph = build_graph(harness)

    initial_state: AgentState = {
        "messages": [],
        "history": [],
        "budget_remaining": 10,
        "best_so_far": None,
        "current_amplitude": None,
        "current_reason": None,
        "converged": False,
        "seed": seed,
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    final_state: AgentState = graph.invoke(initial_state, config=config)  # type: ignore[call-overload]
    return final_state["history"]


def test_same_seed_produces_identical_measurement_history() -> None:
    history_a = _run_once(seed=42)
    history_b = _run_once(seed=42)

    assert len(history_a) == 3
    assert [r.amplitude for r in history_a] == [r.amplitude for r in history_b]
    assert [r.fidelity for r in history_a] == [r.fidelity for r in history_b]
