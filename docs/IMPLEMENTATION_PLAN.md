# BuySpy - Implementation Plan

This document outlines the phased development plan for the BuySpy project, tailored to the structure and tooling provided by the ADK Starter Kit.

---

### Phase 1: Foundation & Local Testing Setup (Week 1)

**Goal:** Understand the starter kit structure and establish a live development loop using the Streamlit playground and a Telegram polling client.

-   **Task 1.1: Project Scaffolding & Familiarization (done)**
    -   Scaffolding is complete using the ADK starter kit.
    -   Review the project structure, especially `app/agent.py`, `pyproject.toml`, and the `Makefile`.
    -   Configure the `.env` file with initial GCP project details and a Telegram Bot token.

-   **Task 1.2: Initial Agent Test (done)**
    -   Run `make install` to set up the virtual environment with `uv`.
    -   Run `make playground`. Interact with the default ReAct agent in the Streamlit UI to confirm the core agent server is working.

-   **Task 1.3: Telegram Polling Integration**
    -   Add dependencies: `uv add python-telegram-bot pydantic-settings`.
    -   **Architecture:** Use proper dependency injection pattern with centralized configuration:
        1.  **Centralized Config** (`app/config.py`): Create Pydantic-based `Settings` class that loads and validates all environment variables from `.env`. Provides type-safe access to configuration with `@lru_cache()` for singleton pattern.
        2.  **Dependency Injection** (`app/dependencies.py`): Create individual getter functions following proper DI patterns:
            - `get_config()`: Returns Settings instance
            - `get_agent_engine()`: Returns singleton agent_engine from `app/agent_engine_app.py`
            - `get_telegram_service()`: Creates TelegramService with injected dependencies
        3.  **Service Module** (`app/services/telegram_service.py`): Already created - handles message routing between Telegram and agent.
        4.  **Entrypoint** (`telegram_bot.py`): Simplified async application that:
            - Uses `get_telegram_service()` to obtain configured service
            - Implements signal handling (SIGTERM/SIGINT) for graceful shutdown
            - Starts polling loop
            - No HTTP server needed - pure Telegram bot application
    -   **Message Flow:** User message → TelegramService → AgentEngineApp → Response → User
    -   **Key Benefits:**
        -   Proper DI: Each getter returns single entity (no tuples)
        -   Type Safety: Pydantic validates configuration at startup
        -   Testability: Easy to mock dependencies
        -   12-Factor App: Configuration via environment variables
        -   Extensibility: Easy to add new config or dependencies
    -   Test the integration: run `uv run python telegram_bot.py` and send a message to your bot.

**Topics Covered:** ADK Starter Kit structure, `uv`, `make`, local development loop, Telegram polling.

---

### Phase 2: The First Agent & Tools (Week 2-3)

**Goal:** Implement the core shopping assistant logic with web search capabilities.

-   **Task 2.1: Customize the Core Agent**
    -   Modify `app/agent.py` to change the agent's core prompt and persona to be a "shopping assistant."
    -   Equip the agent with the **built-in Google Search tool**.

-   **Task 2.2: Test and Refine**
    -   Use the Streamlit playground (`make playground`) for rapid, iterative testing of the agent's search capabilities.
    -   Test the end-to-end flow through the Telegram bot.

-   **Task 2.3: Implement Observability**
    -   The starter kit comes with OpenTelemetry pre-configured.
    -   Run test queries and inspect the logs/traces in the Google Cloud console to understand the agent's reasoning and tool usage.

**Topics Covered:** Agent powered by an LLM, Built-in Tools, Observability (Logging, Tracing).

---

### Phase 3: Personalization & Memory (Week 4)

**Goal:** Give the agent the ability to remember user details across conversations.

-   **Task 3.1: Long-Term Memory Setup**
    -   Set up a Google Cloud Firestore database in your GCP project.
    -   Create a helper module, e.g., `app/app_utils/memory_manager.py`, to handle all interactions with Firestore.

-   **Task 3.2: Implement Memory Tools**
    -   In a new file, e.g., `app/tools/memory_tools.py`, create two **custom tools**: `save_user_preference(key, value)` and `get_user_preference(key)`.
    -   Import and register these tools with your agent in `app/agent.py`.
    -   Update the agent's prompt to proactively ask for the user's name and preferences and use these tools.

**Topics Covered:** Custom Tools, Long-Term Memory (Memory Bank), Sessions & State Management.

---

### Phase 4: The Multi-Agent System (Week 5-6)

**Goal:** Refactor the single agent into a sophisticated, multi-agent system with specialized roles.

-   **Task 4.1: Architect the Multi-Agent System**
    -   Design the interaction flow between the `OrchestratorAgent` and the specialist agents.
    -   Create a new directory `app/specialist_agents/` to house the logic for each specialist.

-   **Task 4.2: Implement Core Specialist Agents & Tools**
    -   The main logic in `app/agent.py` will become the `OrchestratorAgent`.
    -   Implement the `TranslationAgent` with a custom tool calling the Google Translation API (`uv add google-cloud-translate`).
    -   Implement the `ToriSearchAgent` with its custom web scraping tool (`uv add beautifulsoup4 requests`).

-   **Task 4.3: Implement the `ReviewAgent` (NEW)**
    -   Create a new `ReviewAgent` in the `app/specialist_agents/` directory.
    -   **Tool 1 (Product Reviews):** This agent will use the **built-in Google Search tool**. Its prompt will be highly specialized to search for review summaries, pros, and cons of specific products.
    -   **Tool 2 (Shop Ratings):** Enable the Google Places API in your GCP project. Create a new **custom tool** `get_shop_rating(shop_name, location)` that calls the Places API to fetch structured data (rating, review count). Add the necessary client library (`uv add googlemaps`).

-   **Task 4.4: Implement Orchestration Logic**
    -   Write the logic within the `OrchestratorAgent` to delegate tasks to the appropriate specialist agents (including the new `ReviewAgent`).
    -   Implement logic to synthesize results from multiple agents into a single, coherent response.

**Topics Covered:** Multi-agent system (Sequential & Parallel agents), Advanced Custom Tools, **API Integration (Google Places)**.

---

### Phase 5: Final Features & Evaluation (Week 7)

**Goal:** Finalize all MVP features and formally evaluate the agent's performance.

-   **Task 5.1: Implement Comparison Summaries**
    -   Add logic to the `OrchestratorAgent` to recognize comparison requests and prompt the LLM to structure the gathered information into a markdown table.

-   **Task 5.2: Agent Evaluation**
    -   Use the `notebooks/` directory to create an evaluation notebook.
    -   Define a test suite of 10-15 user prompts and an evaluation rubric (Relevance, Accuracy, etc.).
    -   Programmatically run the agent against the test suite and document the results.

-   **Task 5.3: Final Polish & Documentation**
    -   Refine all prompts for performance and persona.
    -   Update the project `README.md` with final instructions.

**Topics Covered:** Agent Evaluation, Context Engineering (prompt refinement).

---

### Phase 6: Deployment Packaging (Week 8)

**Goal:** Package the application for easy deployment on a local server using Docker.

-   **Task 6.1: Finalize the Dockerfile**
    -   Ensure the `Dockerfile` provided by the starter kit is optimized and correctly copies all necessary application code.

-   **Task 6.2: Create Docker Compose Configuration**
    -   Create a `docker-compose.yml` file.
    -   Define the service:
        1.  `telegram-bot`: Builds from the `Dockerfile` and runs `uv run python telegram_bot.py`.
    -   Configure environment variables and volume mounts for the `.env` file.
    -   Ensure proper signal handling for graceful shutdown in containers.

-   **Task 6.3: Document Deployment**
    -   Add clear, concise instructions to the `README.md` on how to deploy the application using `docker-compose up`.