# Langfuse Tracing Setup

This guide walks through enabling Langfuse tracing in the Day 13 Observability Lab.

## Quick Start

### 1. Install Langfuse (already in requirements.txt)

The `langfuse` package is already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Create Langfuse Account

1. Go to [langfuse.com](https://langfuse.com)
2. Sign up for a free account
3. Create a new project
4. Copy your **Public Key** and **Secret Key** from project settings

### 3. Configure Environment

Create a `.env` file in the project root with your Langfuse credentials:

```bash
# .env
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

Or set as environment variables:

```bash
export LANGFUSE_PUBLIC_KEY=pk_...
export LANGFUSE_SECRET_KEY=sk_...
```

### 4. Start the Application

```bash
# The tracing will initialize automatically
uvicorn app.main:app --reload
```

### 5. Verify Tracing is Enabled

```bash
curl http://localhost:8000/health
# Response should show "tracing_enabled": true
```

### 6. Make Test Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "sess456",
    "feature": "product_support",
    "message": "What is your return policy?"
  }'
```

### 7. View Traces

Visit your Langfuse dashboard at [langfuse.com](https://langfuse.com) and navigate to your project. You'll see:

- **Traces**: All requests with complete span hierarchy
- **Latency**: Request timing breakdown
- **Cost**: LLM API cost tracking
- **Metrics**: Quality scores and custom metadata

## Integration Components

### Core Files Modified

1. **app/tracing.py**
   - Langfuse client initialization
   - Context managers: `langfuse_span()`, `langfuse_trace()`
   - Helper: `update_current_span()`, `init_tracing()`

2. **app/main.py**
   - Startup initialization: `init_tracing()`
   - Imports new tracing utilities

3. **app/agent.py**
   - Retrieval span with input/output tracking
   - LLM generation span with cost/token tracking
   - Structured trace updates with metadata

4. **app/middleware.py**
   - HTTP request tracing
   - Response status and latency tracking
   - Correlation ID propagation

## Best Practices Followed

✅ **Structured Tracing**: Input/output tracking on all spans
✅ **Context Propagation**: Automatic trace ID and correlation ID propagation
✅ **Cost Tracking**: LLM cost calculation and tracking
✅ **Metadata**: Rich business and technical metadata
✅ **Error Handling**: Graceful degradation if Langfuse unavailable
✅ **PII Protection**: User IDs are hashed before sending
✅ **Performance**: Async non-blocking implementation
✅ **Conditional**: Only enabled when credentials provided

## Key Tracing Points

### 1. HTTP Request (Middleware)
```
POST /chat
├─ Method, Route, Correlation ID
├─ Status Code, Latency
└─ Error Tracking
```

### 2. Agent Execution (Agent)
```
Chat Request
├─ Retrieval Span
│  ├─ Input: Query
│  └─ Output: Documents, Count
├─ LLM Generation Span
│  ├─ Input: Prompt, Model
│  ├─ Output: Response Text
│  └─ Metrics: Tokens, Cost
└─ Trace Metadata
   ├─ User ID (hashed)
   ├─ Session ID
   ├─ Tags, Features
   └─ Quality Score
```

## Langfuse Dashboard

### Traces View
- See all requests with complete span tree
- Filter by user, session, tags, or time
- View exact inputs/outputs for debugging

### Analytics
- **Cost Analysis**: Spending by model/feature/user
- **Latency Distribution**: Identify bottlenecks
- **Token Usage**: Monitor input/output patterns
- **Error Rates**: Track failures
- **Quality Metrics**: Monitor quality scores

### Debugging
- Drill into individual spans
- Compare traces with/without incidents
- Test with incident injection:
  ```bash
  curl -X POST http://localhost:8000/incidents/latency/enable
  ```

## Troubleshooting

### Traces not appearing?

1. **Check credentials**
   ```bash
   echo $LANGFUSE_PUBLIC_KEY
   echo $LANGFUSE_SECRET_KEY
   ```

2. **Check health endpoint**
   ```bash
   curl http://localhost:8000/health | grep tracing_enabled
   ```

3. **Check logs**
   ```bash
   # Look for "langfuse_initialized" message
   ```

4. **Verify network**
   ```bash
   # Ensure connectivity to Langfuse servers
   curl https://cloud.langfuse.com
   ```

### Performance issues?

- Langfuse SDK batches and sends asynchronously
- Default batch size: 100 spans
- Flush interval: 10 seconds
- No blocking on main request path

### Data privacy?

- User IDs are hashed using SHA256
- Never send raw user identifiers
- All PII is processed before tracing
- Sensitive data removed from logs

## Advanced Configuration

### Custom Langfuse Host

For self-hosted Langfuse:

```bash
LANGFUSE_HOST=https://your-langfuse-instance.com
```

### Trace Filtering

Customize what gets traced in `app/tracing.py`:

```python
def tracing_enabled() -> bool:
    # Could add additional conditions
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
```

### Custom Metadata

Add application-specific metadata:

```python
langfuse_context.update_current_trace(
    metadata={
        "custom_field": "custom_value",
        "app_version": "1.0.0",
        "deployment_region": "us-east-1",
    }
)
```

## Related Documentation

- [Langfuse Integration Details](./langfuse-integration.md)
- [Observability Architecture](./dashboard-spec.md)
- [Monitoring and Alerts](./alerts.md)
