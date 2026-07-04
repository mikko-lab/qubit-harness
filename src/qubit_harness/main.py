"""CLI entry point for the qubit calibration harness."""

import argparse
import os
import sys
import uuid

from dotenv import load_dotenv

from qubit_harness.graph import AgentState, build_graph
from qubit_harness.harness import CalibrationHarness
from qubit_harness.tracing import make_run_config


def _print_summary(final_state: AgentState, trace_enabled: bool) -> None:
    best = final_state.get("best_so_far")
    history = final_state.get("history", [])
    budget_remaining = final_state.get("budget_remaining", 0)

    print("\n── Calibration complete ──────────────────────────────")
    if best:
        print(f"  Best amplitude   : {best.amplitude:.4f}")
        print(f"  Best fidelity    : {best.fidelity:.4f}")
    else:
        print("  No measurements completed.")
    print(f"  Measurements used: {len(history)}")
    print(f"  Budget remaining : {budget_remaining}")
    if trace_enabled and os.getenv("LANGFUSE_PUBLIC_KEY"):
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        print(f"  Langfuse trace   : {host}/traces")
    print("──────────────────────────────────────────────────────\n")


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Qubit calibration harness demo")
    parser.add_argument("--budget", type=int, default=15, help="Max measurements (default 15)")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    parser.add_argument("--no-trace", action="store_true", help="Disable Langfuse tracing")
    args = parser.parse_args()

    trace_enabled = not args.no_trace
    session_id = str(uuid.uuid4())

    harness = CalibrationHarness(session_budget=args.budget)
    graph = build_graph(harness)

    initial_state: AgentState = {
        "messages": [],
        "history": [],
        "budget_remaining": args.budget,
        "best_so_far": None,
        "current_amplitude": None,
        "current_reason": None,
        "converged": False,
        "seed": args.seed,
    }

    run_config = make_run_config(session_id, trace_enabled)

    print(f"Starting calibration  budget={args.budget}  trace={'on' if trace_enabled else 'off'}")
    print()

    try:
        final_state: AgentState = graph.invoke(initial_state, config=run_config)  # type: ignore[call-overload]
    except Exception as exc:
        print(f"Error during calibration: {exc}", file=sys.stderr)
        sys.exit(1)

    _print_summary(final_state, trace_enabled)


if __name__ == "__main__":
    main()
