from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from typing import Any, Generator

import structlog
from structlog.contextvars import get_contextvars
from langfuse import get_client
from langfuse import Langfuse
# from langfuse.decorators import observe, langfuse_context

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()
    Langfuse = None  # type: ignore


# Initialize Langfuse client
def _init_langfuse() -> Langfuse | None:
    """Initialize Langfuse client if credentials are available."""
    if not tracing_enabled():
        return None
    try:
        return Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception:
        return None


langfuse_client: Langfuse | None = None


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def init_tracing() -> None:
    """Initialize Langfuse tracing at application startup."""
    global langfuse_client

    try:
        langfuse_client = get_client()
        is_ready = langfuse_client.auth_check()

        logger.info(
            "langfuse_initialized",
            status="enabled" if is_ready else "disabled"
        )

    except Exception as e:
        logger.error(
            "langfuse_init_failed",
            error=str(e)
        )
        langfuse_client = None


def get_langfuse_client() -> Langfuse | None:
    """Get the initialized Langfuse client."""
    return langfuse_client



logger = structlog.get_logger("trace")


def _new_span_id() -> str:
    return f"span-{uuid.uuid4().hex[:8]}"


def current_trace_id() -> str:
    context = get_contextvars()
    return context.get("correlation_id", "unknown")


def start_span(
    service: str,
    event: str,
    parent_span_id: str | None = None,
    **kwargs: Any,
) -> str:
    trace_id = current_trace_id()
    span_id = _new_span_id()

    logger.info(
        "span_start",
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        service=service,
        trace_event=event,
        **kwargs,
    )
    return span_id


def end_span(
    service: str,
    event: str,
    span_id: str,
    parent_span_id: str | None = None,
    **kwargs: Any,
) -> None:
    trace_id = current_trace_id()

    logger.info(
        "span_end",
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        service=service,
        trace_event=event,
        **kwargs,
    )


def trace_log(
    event: str,
    service: str,
    span_id: str | None = None,
    parent_span_id: str | None = None,
    **kwargs: Any,
) -> None:
    trace_id = current_trace_id()

    logger.info(
        "trace_log",
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        service=service,
        trace_event=event,
        **kwargs,
    )


@contextmanager
def langfuse_span(
    name: str,
    input: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
) -> Generator[Any, None, None]:
    """Context manager for creating Langfuse spans with structured tracing.
    
    Best practice: Use this for automatic span lifecycle management with proper
    error handling and input/output tracking.
    
    Example:
        with langfuse_span("llm_call", input={"prompt": "..."}) as span:
            result = llm.generate(prompt)
            span.update(output=result)
    """
    if not langfuse_client:
        yield None
        return
    
    try:
        trace_id = current_trace_id()
        span = langfuse_client.span(
            name=name,
            input=input,
            metadata=metadata or {},
            session_id=session_id,
            user_id=user_id,
            tags=tags or [],
            trace_id=trace_id,
        )
        yield span
        span.end()
    except Exception as e:
        logger.error("langfuse_span_error", name=name, error=str(e))
        yield None


@contextmanager
def langfuse_trace(
    name: str,
    input: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
) -> Generator[Any, None, None]:
    """Context manager for creating root-level Langfuse traces.
    
    Best practice: Use for top-level operations like API requests or agent runs.
    """
    if not langfuse_client:
        yield None
        return
    
    try:
        trace = langfuse_client.trace(
            name=name,
            input=input,
            metadata=metadata or {},
            session_id=session_id,
            user_id=user_id,
            tags=tags or [],
        )
        yield trace
        trace.end()
    except Exception as e:
        logger.error("langfuse_trace_error", name=name, error=str(e))
        yield None


def update_current_span(
    input: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    status: str | None = None,
    level: str | None = None,
    cost_usd: float | None = None,
    latency_ms: float | None = None,
    **kwargs: Any,
) -> None:
    """Update the current observation with structured data.
    
    Best practice: Call this to record completion details and metrics.
    """
    if not langfuse_client:
        return
    
    try:
        updates = {}
        if input is not None:
            updates["input"] = input
        if output is not None:
            updates["output"] = output
        if metadata is not None:
            updates["metadata"] = metadata
        if status is not None:
            updates["status"] = status
        if level is not None:
            updates["level"] = level
        if cost_usd is not None:
            # Record cost as metadata to avoid overwriting usage
            if "metadata" not in updates:
                updates["metadata"] = {}
            updates["metadata"]["cost_usd"] = cost_usd
        if latency_ms is not None:
            if "metadata" not in updates:
                updates["metadata"] = {}
            updates["metadata"]["latency_ms"] = latency_ms
        
        for key, value in kwargs.items():
            if "metadata" not in updates:
                updates["metadata"] = {}
            updates["metadata"][key] = value
        
        langfuse_context.update_current_observation(**updates)
    except Exception as e:
        logger.error("update_span_error", error=str(e))
