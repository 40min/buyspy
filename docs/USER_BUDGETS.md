# Refactoring Plan: Redis-Based Daily Budget Strategy

## 1. Executive Summary & Goals
The objective is to implement a robust, concurrency-safe rate-limiting system using Redis. This will limit users to a configurable number of messages within a specific time window (e.g., 30 messages per 24 hours).

**Key Goals:**
*   Replace naive local file storage with Redis for atomic counters.
*   Implement a "Time-To-Live" (TTL) mechanism to auto-reset counters (Daily Limit).
*   Provide tooling (Script & Makefile) to inspect current user usage and remaining quotas.

## 2. Current Situation Analysis
The current `TelegramService` processes all messages without restriction. No rate-limiting infrastructure exists. Configuration is managed via `app/config.py`.

## 3. Proposed Solution

### 3.1. Architectural Overview
*   **Infrastructure**: A Redis container will be added to the stack.
*   **Logic**: A `BudgetService` will handle atomic increments. When a counter is initialized (first message), a TTL (24h) is applied.
*   **Integration**: `TelegramService` consults `BudgetService` before processing.
*   **Reporting**: A script connects to Redis to list active users, current counts, and time until reset.

### 3.2. Key Components
*   **`BudgetService`**: Wrapper for Redis operations (`INCR`, `EXPIRE`).
*   **`Redis`**: Stores keys in format `budget:{user_id}`.
*   **`Settings`**: Updated with Redis config and limit parameters.

### 3.3. Detailed Action Plan

#### Phase 1: Infrastructure & Configuration
*   **Task 1.1: Docker Configuration**
    *   **File**: `docker-compose.yml` (Create or Update)
    *   **Action**: Add a `redis` service (image: `redis:alpine`). Configure `app` service to link to `redis`.
*   **Task 1.2: Update Configuration**
    *   **File**: `app/config.py`
    *   **Action**: Add the following fields to `Settings`:
        *   `REDIS_HOST`: (str, default "redis")
        *   `REDIS_PORT`: (int, default 6379)
        *   `MESSAGE_LIMIT`: (int, default 30)
        *   `MESSAGE_LIMIT_TTL`: (int, default 86400) - 24 hours in seconds.
        *   `WHITELISTED_USERS`: (str, default "") - Comma-separated usernames.

#### Phase 2: Budget Service Implementation
*   **Task 2.1: Create Budget Service**
    *   **File**: `app/services/budget_service.py`
    *   **Action**: Implement `BudgetService` class.
        *   **Inputs**: Redis client, Limit, TTL, Whitelist.
        *   **Method**: `check_and_increment(user_id: str) -> bool`
        *   **Logic**:
            1.  If `user_id` in whitelist, return `True`.
            2.  Perform atomic `INCR budget:{user_id}`.
            3.  If result is `1` (new counter), perform `EXPIRE budget:{user_id} {ttl}`.
            4.  Return `True` if result <= limit, else `False`.

#### Phase 3: Dependencies & Integration
*   **Task 3.1: Update Dependencies**
    *   **File**: `app/app_utils/.requirements.txt`
    *   **Action**: Add `redis`.
*   **Task 3.2: Update Dependency Injection**
    *   **File**: `app/dependencies.py`
    *   **Action**:
        *   Add `get_redis_client()`: Returns `redis.Redis`.
        *   Add `get_budget_service()`: Injects settings and redis client.
        *   Update `get_telegram_service()`: Inject `get_budget_service`.
*   **Task 3.3: Integrate into Telegram Service**
    *   **File**: `app/services/telegram_service.py`
    *   **Action**:
        *   Update `__init__` to store `budget_service`.
        *   In `handle_message`: Before any processing, call `budget_service.check_and_increment`.
        *   If it returns `False`, log rejection and return immediately.

#### Phase 4: Tooling & Verification
*   **Task 4.1: Create Status Script**
    *   **File**: `scripts/check_budget.py`
    *   **Action**:
        *   Connect to Redis using env vars.
        *   Iterate keys `budget:*`.
        *   For each key: get value (count) and get TTL (time remaining).
        *   Print table: `User ID | Count | TTL (sec)`.
*   **Task 4.2: Add Makefile Targets**
    *   **File**: `Makefile`
    *   **Action**:
        *   `budget-status`: Runs script via local python.
        *   `budget-status-container`: Runs script via `docker compose exec`.

## 4. Key Considerations & Risk Mitigation
### 4.1. Technical Risks
*   **Redis Persistence**: By default, Redis holds data in memory. If the container restarts, counts might reset.
    *   *Mitigation*: Use Redis AOF (Append Only File) or RDB persistence if strict quota enforcement across restarts is required. For this "naive" budget implementation, memory-only is acceptable.
*   **Timezone/Reset**: The logic uses a "sliding window start" (24h from first message). It does not reset at midnight.
    *   *Mitigation*: This is standard for simple rate limiting and usually fairer to users.

### 4.2. Dependencies
*   `redis` python package.
*   Docker/Podman runtime.

## 5. Success Metrics
*   Users are blocked after 30 messages.
*   Counters expire and reset automatically after 24 hours of inactivity.
*   Administration can view active quotas via command line.

## 6. Assumptions Made
*   The `user_id` from Telegram is stable.
*   The environment provides network access between the App container and Redis container.

## 7. Open Questions
*   None.

---

## 8. File Examples (For Logic Reference)

### `app/services/budget_service.py` (Pseudocode)
```python
import redis

class BudgetService:
    def __init__(self, redis_client, limit, ttl, whitelist):
        self.redis = redis_client
        self.limit = limit
        self.ttl = ttl
        self.whitelist = whitelist

    def check_and_increment(self, user_id: str) -> bool:
        if user_id in self.whitelist:
            return True

        key = f"budget:{user_id}"
        # Pipeline ensures atomicity of increment
        count = self.redis.incr(key)

        # Set expiry only on first increment
        if count == 1:
            self.redis.expire(key, self.ttl)

        return count <= self.limit
```

### `scripts/check_budget.py` (Pseudocode)
```python
import os
import redis
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

print(f"{'USER':<15} | {'COUNT':<5} | {'TTL (s)':<10}")
for key in r.scan_iter("budget:*"):
    count = r.get(key)
    ttl = r.ttl(key)
    uid = key.split(":")[1]
    print(f"{uid:<15} | {count:<5} | {ttl:<10}")
```
