from __future__ import annotations

import os
import re
import uuid
from contextlib import contextmanager
from typing import Any, Generator

import structlog
from structlog.contextvars import get_contextvars
from langfuse import Langfuse, propagate_attributes

logger = structlog.get_logger("trace")

langfuse_client: Langfuse | None = None

# Simple detector rules aligned with validate_logs.py behavior
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
LONG_DIGITS_RE = re.compile(r"\b\d{13,19}\b")


def tracing_enabled() -> bool:
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
        and os.getenv("LANGFUSE_BASE_URL")
    )


def init_tracing() -> None:
    global langfuse_client

    if not tracing_enabled():
        logger.warning(
            "langfuse_disabled",
            reason="missing LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY or LANGFUSE_BASE_URL",
        )
        langfuse_client = None
        return

    try:
        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL"),
            debug=os.getenv("LANGFUSE_DEBUG", "false").lower() == "true",
        )

        logger.info(
            "langfuse_initialized",
            status="enabled",
            host=os.getenv("LANGFUSE_BASE_URL"),
        )
    except Exception as exc:
        logger.error(
            "langfuse_init_failed",
            error=str(exc),
        )
        langfuse_client = None


def get_langfuse_client() -> Langfuse | None:
    return langfuse_client


def current_trace_id() -> str:
    context = get_contextvars()
    return context.get("correlation_id", "unknown")


def _new_span_id() -> str:
    return f"span-{uuid.uuid4().hex[:8]}"


def _redact_string(value: str) -> str:
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = LONG_DIGITS_RE.sub("[REDACTED_NUMBER]", value)
    return value


def _scrub_for_logs(value: Any) -> Any:
    """Recursively scrub likely-PII from structured logs."""
    if value is None:
        return None

    if isinstance(value, str):
        return _redact_string(value)

    if isinstance(value, dict):
        scrubbed: dict[str, Any] = {}
        for k, v in value.items():
            key = str(k).lower()

            # Aggressive protection for common sensitive keys
            if key in {
                "message",
                "prompt",
                "input",
                "answer",
                "response",
                "context",
                "email",
                "phone",
                "card",
                "credit_card",
                "account_number",
                "bank_account",
                "customer_email",
            }:
                scrubbed[k] = "[REDACTED]"
            else:
                scrubbed[k] = _scrub_for_logs(v)
        return scrubbed

    if isinstance(value, (list, tuple, set)):
        return [_scrub_for_logs(v) for v in value]

    return value


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
        **_scrub_for_logs(kwargs),
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
        **_scrub_for_logs(kwargs),
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
        **_scrub_for_logs(kwargs),
    )


@contextmanager
def langfuse_root_span(
    *,
    name: str,
    input: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
) -> Generator[Any, None, None]:
    client = get_langfuse_client()
    if not client:
        yield None
        return

    # Keep Langfuse metadata lightweight and non-sensitive
    meta = _scrub_for_logs({
        "correlation_id": current_trace_id(),
        **(metadata or {}),
    })

    safe_input = _scrub_for_logs(input) if input is not None else None

    with client.start_as_current_observation(
        as_type="span",
        name=name,
        input=safe_input,
        metadata=meta,
    ) as root_span:
        with propagate_attributes(
            trace_name=name,
            user_id=user_id,
            session_id=session_id,
            tags=tags or [],
            metadata=meta,
        ):
            yield root_span