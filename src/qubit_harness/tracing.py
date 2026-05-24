"""Langfuse tracing setup for LangGraph runs."""

import os
from typing import Any


def get_callback_handler() -> Any | None:
    """Return a configured Langfuse CallbackHandler, or None if keys are absent."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        return None

    from langfuse.langchain import CallbackHandler

    # secret_key and host are read from LANGFUSE_SECRET_KEY / LANGFUSE_HOST env vars
    return CallbackHandler(public_key=public_key)


def make_run_config(session_id: str, trace_enabled: bool) -> dict[str, Any]:
    """Build LangGraph run config with optional Langfuse callbacks."""
    config: dict[str, Any] = {
        "configurable": {"thread_id": session_id},
    }

    if trace_enabled:
        handler = get_callback_handler()
        if handler is not None:
            config["callbacks"] = [handler]

    return config
