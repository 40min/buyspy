# Timeout Configuration for Agent Processing

## Overview

The BuySpy Telegram bot now includes a configurable timeout for agent processing to prevent hanging on slow or complex requests. This ensures users receive feedback even when the agent takes longer than expected to process their request.

## Current Configuration

- **Default Timeout**: 600 seconds (10 minutes)
- **Applied to**: Agent message processing via `async_stream_query`
- **Location**: `app/services/telegram_service.py` and `app/dependencies.py`

## How It Works

### 1. Timeout Parameter
The `TelegramService` constructor now accepts a `timeout_seconds` parameter:

```python
def __init__(self, bot_token: str, agent_engine: AgentEngineApp, timeout_seconds: int = 600):
```

### 2. Processing Logic
- Agent processing is wrapped with `asyncio.wait_for()`
- If processing exceeds the timeout, the task is cancelled
- User receives a helpful timeout message
- All operations are properly logged

### 3. Timeout Handling
When a timeout occurs:
- The processing task is cancelled if still running
- A user-friendly message is sent: *"I apologize, but my processing is taking longer than expected. Please try your request again, or simplify your question if possible."*
- The event is logged for monitoring

## Customizing the Timeout

### Option 1: Modify Dependencies (Recommended)
Edit `app/dependencies.py` and change the timeout value:

```python
return TelegramService(
    bot_token=config.telegram_bot_token,
    agent_engine=engine,
    timeout_seconds=300  # 5 minutes instead of 10
)
```

### Option 2: Environment Variable (Advanced)
To make it configurable via environment variables:

1. Add to `app/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    agent_timeout_seconds: int = 600
```

2. Update `app/dependencies.py`:
```python
return TelegramService(
    bot_token=config.telegram_bot_token,
    agent_engine=engine,
    timeout_seconds=config.agent_timeout_seconds
)
```

### Option 3: Per-Request Timeout
For different timeouts based on message type or user, modify `handle_message()`:

```python
# Determine timeout based on message content
timeout = 300 if "quick" in user_message.lower() else 600

processing_task = asyncio.create_task(
    self._process_agent_response(user_message, user_id, session_id)
)

response_text, event_count = await asyncio.wait_for(
    processing_task, timeout=timeout
)
```

## Monitoring and Logging

The timeout implementation includes comprehensive logging:

- **Info Level**: Session ID creation and response sending
- **Warning Level**: Timeout events and processing warnings
- **Error Level**: General processing errors

Example log entries:
```
INFO: Using session ID: 12345
WARNING: Agent processing timed out after 600 seconds for user 67890
ERROR: Error during agent processing: [exception details]
```

## Best Practices

1. **Reasonable Timeouts**:
   - 5-10 minutes is appropriate for most agent processing
   - Too short may interrupt legitimate complex queries
   - Too long may frustrate users waiting for responses

2. **User Experience**:
   - Always provide helpful timeout messages
   - Consider suggesting users simplify their requests
   - Monitor timeout frequency to identify performance issues

3. **Performance Monitoring**:
   - Track timeout occurrences in logs
   - Analyze which types of requests commonly timeout
   - Consider optimizing slow-running agents or adding caching

## Testing the Timeout

To test the timeout functionality:

1. **Unit Tests**: Existing tests should continue to work since timeout_seconds has a default value
2. **Integration Tests**: Modify test cases to use shorter timeouts for faster testing
3. **Manual Testing**: Send complex requests that might take longer than the timeout

## Backward Compatibility

The timeout implementation is fully backward compatible:
- Default timeout (600 seconds) applies if not specified
- Existing code using `TelegramService(bot_token, agent_engine)` continues to work
- Test files don't need modification
