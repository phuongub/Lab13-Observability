from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from .tracing import end_span, start_span, trace_log, langfuse_span


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        correlation_id = request.headers.get("x-request-id")
        if not correlation_id:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        route = request.url.path
        method = request.method

        bind_contextvars(
            correlation_id=correlation_id,
            route=route,
            method=method,
        )
        request.state.correlation_id = correlation_id

        api_span_id = start_span(
            service="api_gateway",
            event="request",
            route=route,
            method=method,
        )

        trace_log(
            event="request_received",
            service="api_gateway",
            span_id=api_span_id,
            parent_span_id=None,
            route=route,
            method=method,
        )

        # Create Langfuse span for HTTP request with proper metadata
        with langfuse_span(
            name=f"{method} {route}",
            input={"path": route, "method": method},
            metadata={
                "correlation_id": correlation_id,
                "path": route,
                "method": method,
            },
            tags=["http", method.lower()],
        ) as http_span:
            start = time.perf_counter()
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start) * 1000

            # Update span with response details
            if http_span:
                http_span.update(
                    output={"status_code": response.status_code},
                    metadata={
                        "status_code": response.status_code,
                        "latency_ms": round(process_time_ms, 2),
                    },
                    level="INFO" if response.status_code < 400 else "WARNING",
                )

        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(round(process_time_ms, 2))

        trace_log(
            event="response_sent",
            service="api_gateway",
            span_id=api_span_id,
            parent_span_id=None,
            route=route,
            method=method,
            status_code=response.status_code,
            latency_ms=round(process_time_ms, 2),
        )

        end_span(
            service="api_gateway",
            event="response",
            span_id=api_span_id,
            parent_span_id=None,
            route=route,
            method=method,
            status_code=response.status_code,
            latency_ms=round(process_time_ms, 2),
        )

        return response