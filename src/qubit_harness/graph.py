"""LangGraph calibration loop — state machine with in-memory checkpointing."""

import os
import re
from typing import Annotated, Literal, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from qubit_harness.harness import CalibrationHarness
from qubit_harness.models import MeasurementResult
from qubit_harness.tools import run_measurement

SYSTEM_PROMPT = """\
You are a qubit calibration agent. Your task: find the pulse amplitude \
in [0.0, 1.0] that maximises fidelity within the given measurement budget.

Rules:
- Each response must contain exactly one proposed amplitude (a float) and \
a one-sentence rationale.
- Base every proposal on the measurement history. Prefer bisection or \
Gaussian-process-style reasoning over random search.
- Never repeat an amplitude already in the history.
- When budget_remaining <= 2 or you are confident in the optimum, output \
CONVERGED: <amplitude> instead of a new proposal.

Do not write summaries, greetings, or explanations beyond the rationale.\
"""

_CONVERGED_RE = re.compile(r"CONVERGED\s*:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_PROPOSE_RE = re.compile(r"\b([0-9]*\.?[0-9]+)\b")


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    history: list[MeasurementResult]
    budget_remaining: int
    best_so_far: MeasurementResult | None
    current_amplitude: float | None
    current_reason: str | None
    converged: bool
    seed: int | None


def _format_history(history: list[MeasurementResult], budget_remaining: int) -> str:
    if not history:
        lines = ["No measurements yet."]
    else:
        lines = [
            f"  amplitude={r.amplitude:.4f}  fidelity={r.fidelity:.4f}"
            for r in history
        ]
    return (
        f"Budget remaining: {budget_remaining}\n"
        f"Measurement history ({len(history)} points):\n"
        + "\n".join(lines)
    )


def _parse_response(text: str) -> tuple[bool, float | None, str | None]:
    """Return (converged, amplitude, reason)."""
    converged_match = _CONVERGED_RE.search(text)
    if converged_match:
        return True, float(converged_match.group(1)), None

    numbers = _PROPOSE_RE.findall(text)
    amplitude = None
    for n in numbers:
        val = float(n)
        if 0.0 <= val <= 1.0:
            amplitude = val
            break

    reason = text.strip().split("\n")[0][:200] if text.strip() else None
    return False, amplitude, reason


def build_graph(
    harness: CalibrationHarness,
    model: str | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    """Build and compile the calibration StateGraph."""
    llm = ChatAnthropic(  # type: ignore[call-arg]
        model=model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        max_tokens=256,
    )

    def propose_parameter(state: AgentState) -> dict:  # type: ignore[type-arg]
        human_msg = HumanMessage(content=_format_history(
            state["history"], state["budget_remaining"]
        ))
        response: AIMessage = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), human_msg])
        converged, amplitude, reason = _parse_response(str(response.content))
        return {
            "messages": [human_msg, response],
            "current_amplitude": amplitude,
            "current_reason": reason,
            "converged": converged,
        }

    def execute_measurement(state: AgentState) -> dict:  # type: ignore[type-arg]
        if state["converged"] or state["current_amplitude"] is None:
            return {}
        base_seed = state.get("seed")
        call_seed = None if base_seed is None else base_seed + len(state["history"])
        result = run_measurement(
            harness, state["current_amplitude"], state["current_reason"], seed=call_seed
        )
        return {
            "history": state["history"] + [result],
            "budget_remaining": state["budget_remaining"] - 1,
        }

    def analyze_result(state: AgentState) -> dict:  # type: ignore[type-arg]
        if not state["history"]:
            return {}
        best = max(state["history"], key=lambda r: r.fidelity)
        return {"best_so_far": best}

    def decide_next(state: AgentState) -> Literal["propose_parameter", "__end__"]:
        if state["converged"] or state["budget_remaining"] <= 0:
            return END  # type: ignore[return-value]
        return "propose_parameter"

    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("propose_parameter", propose_parameter)
    graph.add_node("execute_measurement", execute_measurement)
    graph.add_node("analyze_result", analyze_result)

    graph.set_entry_point("propose_parameter")
    graph.add_edge("propose_parameter", "execute_measurement")
    graph.add_edge("execute_measurement", "analyze_result")
    graph.add_conditional_edges("analyze_result", decide_next)

    return graph.compile(checkpointer=MemorySaver())
