# Langfuse Integration Guide

This document describes the Langfuse tracing integration implemented in the Day 13 Observability Lab, following best practices from the Langfuse framework.

## Overview

Langfuse is integrated into this application to provide comprehensive observability for AI/LLM applications with structured tracing, monitoring, and analytics capabilities. The integration covers:

- **Request tracing**: HTTP request lifecycle
- **Agent execution**: End-to-end LLM agent operations
- **Component-level spans**: Retrieval, LLM generation, quality scoring
- **Structured metadata**: Cost, latency, token usage, quality metrics
- **Error tracking**: Automatic error capture and logging

## Setup & Configuration

### Environment Variables

Configure the following environment variables to enable Langfuse tracing:

```bash
# Required for Langfuse integration
LANGFUSE_PUBLIC_KEY=<your-public-key>
LANGFUSE_SECRET_KEY=<your-secret-key>

# Optional
LANGFUSE_HOST=https://cloud.langfuse.com  # Default: Langfuse Cloud
```

### Initialization

Langfuse is initialized at application startup:

```python
# In main.py
from .tracing import init_tracing

@app.on_event("startup")
async def startup() -> None:
    init_tracing()
    # ... other startup code
```

## Best Practices Implemented

### 1. Context Propagation

**Pattern**: Automatic correlation ID propagation through structured context

The `CorrelationIdMiddleware` ensures trace context is maintained across the request lifecycle:

```python
# Each request gets a unique correlation ID
# Automatically propagated through structlog context
bind_contextvars(
    correlation_id=correlation_id,
    route=route,
    method=method,
)
```

**Why**: Enables end-to-end request tracking across all spans and logs.

### 2. Span Hierarchy

**Pattern**: Parent-child span relationships for nested operations

Example structure:
```
HTTP Request (POST /chat)
├── Agent Execution
│   ├── Retrieval Span
│   │   └── query: "user message"
│   │   └── output: [docs]
│   ├── LLM Generation Span
│   │   └── input: "prompt"
│   │   └── output: "answer"
│   └── Quality Scoring
└── Response (status_code: 200)
```

**Implementation**:
```python
with langfuse_span(
    name="retrieval",
    input={"query": message},
    metadata={"feature": feature},
) as retrieval_span:
    docs = retrieve(message)
    retrieval_span.update(
        output={"doc_count": len(docs)},
        metadata={"retrieved_doc_count": len(docs)}
    )
```

**Why**: Provides detailed visibility into request flow and makes it easy to identify bottlenecks.

### 3. Structured Input/Output Tracking

**Pattern**: Explicit input and output capture for all operations

All spans track their inputs and outputs:

```python
# Retrieval span
with langfuse_span(
    name="retrieval",
    input={"query": message},  # What goes in
    tags=["retrieval", feature],
) as retrieval_span:
    result = retrieve(message)
    retrieval_span.update(
        output={"doc_count": len(result)},  # What comes out
        metadata={"retrieved_doc_count": len(result)}
    )
```

**Why**: Enables debugging, quality analysis, and model retraining data collection.

### 4. Rich Metadata

**Pattern**: Comprehensive metadata for analytics and debugging

Every span includes relevant business and technical metadata:

```python
langfuse_context.update_current_trace(
    user_id=user_id_hash,           # User for cohort analysis
    session_id=session_id,           # Session grouping
    tags=["lab", feature, model],    # For filtering and grouping
    metadata={                        # Rich business metrics
        "quality_score": quality_score,
        "feature": feature,
        "model": model,
    },
)
```

**Why**: Enables powerful analytics, filtering, and debugging at scale.

### 5. Cost and Performance Tracking

**Pattern**: Automatic cost and latency calculation

```python
update_current_span(
    cost_usd=cost_usd,              # LLM cost
    latency_ms=latency_ms,          # Request duration
    metadata={                       # Additional metrics
        "tokens_in": input_tokens,
        "tokens_out": output_tokens,
        "quality_score": quality_score,
    }
)

langfuse_context.update_current_observation(
    usage_details={                  # Token usage
        "input": response.usage.input_tokens,
        "output": response.usage.output_tokens,
    }
)
```

**Why**: Enables cost analysis, ROI tracking, and performance optimization.

### 6. Error Handling

**Pattern**: Graceful degradation with automatic error capture

```python
try:
    # Langfuse operations
    with langfuse_span(...) as span:
        # ... span operations
except Exception as e:
    # Automatic error logging
    logger.error("langfuse_span_error", name=name, error=str(e))
    # Code continues without Langfuse
```

**Why**: Ensures Langfuse issues never break the main application.

### 7. Conditional Initialization

**Pattern**: Langfuse only activates if credentials are available

```python
def tracing_enabled() -> bool:
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") 
        and os.getenv("LANGFUSE_SECRET_KEY")
    )

def _init_langfuse() -> Langfuse | None:
    if not tracing_enabled():
        return None
    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    )
```

**Why**: Development works without Langfuse credentials; production enables when available.

## Core API

### Context Managers

#### `langfuse_span(name, input=None, metadata=None, ...)`

Create a nested span within a trace:

```python
with langfuse_span(
    name="operation_name",
    input={"param": value},
    metadata={"key": "value"},
    session_id=session_id,
    user_id=user_id,
    tags=["tag1", "tag2"],
) as span:
    # Perform operation
    result = do_something()
    
    # Update with results
    span.update(
        output={"result": result},
        metadata={"execution_time": 100}
    )
```

#### `langfuse_trace(name, input=None, metadata=None, ...)`

Create a root-level trace (rarely needed in middleware-based setup):

```python
with langfuse_trace(
    name="main_operation",
    input={"data": input_data},
    session_id=session_id,
    user_id=user_id,
) as trace:
    result = perform_operation()
    trace.end()
```

### Helper Functions

#### `update_current_span(input=None, output=None, metadata=None, ...)`

Update the current observation with structured data:

```python
update_current_span(
    input={"message": message},
    output={"answer": response},
    metadata={"quality_score": 0.85},
    cost_usd=0.0001,
    latency_ms=245
)
```

#### `init_tracing()`

Initialize Langfuse at application startup:

```python
@app.on_event("startup")
async def startup():
    init_tracing()
```

#### `tracing_enabled()`

Check if Langfuse is properly configured:

```python
if tracing_enabled():
    # Langfuse is available
    pass
```

## Integration Examples

### HTTP Middleware

The middleware automatically traces all HTTP requests:

```python
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        with langfuse_span(
            name=f"{method} {route}",
            input={"path": route, "method": method},
            tags=["http", method.lower()],
        ) as http_span:
            response = await call_next(request)
            http_span.update(
                output={"status_code": response.status_code},
                metadata={"latency_ms": process_time_ms}
            )
        return response
```

### Agent Execution

Agent operations are traced with retrieval and LLM spans:

```python
@observe()  # Langfuse decorator
def run(self, user_id: str, feature: str, message: str) -> AgentResult:
    with langfuse_span(
        name="retrieval",
        input={"query": message},
        tags=["retrieval", feature],
    ) as retrieval_span:
        docs = retrieve(message)
        retrieval_span.update(output={"doc_count": len(docs)})
    
    with langfuse_span(
        name="llm_generation",
        input={"prompt": prompt, "model": self.model},
        tags=["llm", self.model],
    ) as llm_span:
        response = self.llm.generate(prompt)
        llm_span.update(output={"text": response.text})
    
    # Update trace metadata
    langfuse_context.update_current_trace(
        user_id=user_id,
        session_id=session_id,
        tags=["lab", feature, self.model],
    )
    
    return AgentResult(...)
```

## Viewing Traces in Langfuse

Once integrated and running:

1. **Traces**: View complete request traces with all spans
2. **Spans**: Drill down into individual operations
3. **Metrics**: Analyze cost, latency, token usage
4. **Sessions**: Group traces by user session
5. **Models**: Compare performance across LLM models
6. **Quality**: Track quality scores and other custom metrics

### Dashboard Features

- **Latency Distribution**: Identify slow operations
- **Cost Analysis**: Track spending by model/feature
- **Error Rate**: Monitor failure rates
- **Token Usage**: Analyze input/output token patterns
- **Quality Trends**: Track quality metric changes over time

## Testing

The implementation includes fallback dummy implementations for when Langfuse is not configured:

```python
try:
    from langfuse.decorators import observe, langfuse_context
except Exception:
    # Dummy implementations that do nothing
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    langfuse_context = _DummyContext()
```

This ensures the application works without Langfuse but gains full tracing when configured.

## Troubleshooting

### Traces Not Appearing

1. Verify environment variables are set correctly
2. Check `POST /health` endpoint for `tracing_enabled: true`
3. Ensure network access to Langfuse service
4. Check application logs for initialization messages

### Performance Impact

The Langfuse SDK sends traces asynchronously:
- Minimal impact on request latency
- Non-blocking by design
- Configurable batch sizes and flush intervals

### Privacy & PII

The application implements PII hashing before sending traces:

```python
from .pii import hash_user_id

user_id_hash = hash_user_id(user_id)  # Never send raw user IDs
```

## References

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)
- [Langfuse Best Practices](https://langfuse.com/docs/sdk/best-practices)
- Application files:
  - `app/tracing.py` - Core tracing module
  - `app/agent.py` - Agent with LLM/retrieval tracing
  - `app/middleware.py` - HTTP request tracing
  - `app/main.py` - Initialization
