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
    -   Add `python-telegram-bot` to the project dependencies using `uv add python-telegram-bot`.
    -   Create a new script: `scripts/run_telegram_bot.py`.
    -   Implement a basic polling loop in this script using `python-telegram-bot`. The script should:
        1.  Fetch new messages from Telegram.
        2.  For each message, make an HTTP request to the local agent server (running via `make playground`).
        3.  Send the agent's response back to the user on Telegram.
    -   Test the full loop: run `make playground` in one terminal, `uv run python scripts/run_telegram_bot.py` in another, and send a message to your bot.

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
    -   Define two services:
        1.  `agent-server`: Builds from the `Dockerfile` and runs the FastAPI app.
        2.  `telegram-poller`: Also builds from the `Dockerfile` but overrides the command to run `uv run python scripts/run_telegram_bot.py`.
    -   Configure networking so the `telegram-poller` can communicate with the `agent-server`.

-   **Task 6.3: Document Deployment**
    -   Add clear, concise instructions to the `README.md` on how to deploy the application using `docker-compose up`.