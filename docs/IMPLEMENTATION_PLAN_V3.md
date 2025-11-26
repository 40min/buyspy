# Refactoring/Design Plan: BuySpy - Implementation Plan V3

## 1. Executive Summary & Goals
This revised plan updates the roadmap to reflect the current state of the BuySpy Multi-Agent System. The core **Orchestration** and **Global Shopping/Research** capabilities have been successfully implemented.

The immediate focus shifts to **State Management (Memory)** to transform the stateless agents into a context-aware concierge. The **Local Market (Tori.fi)** functionality is recognized as a valid requirement but is currently deferred (Low Priority).

**Key Goals:**
1.  **Enable Long-Term Memory:** Implement Firestore to persist user preferences and interaction history.
2.  **Enable Session Context:** Implement short-term memory for conversation continuity.
3.  **Backlog Local Search:** Define the roadmap for the deferred Tori.fi integration.

## 2. Current Situation Analysis
*   **Implemented Architecture:**
    *   **Orchestrator:** `app/subagents/orchestrator` is functional, coordinating sub-agents.
    *   **Specialists:** `research_agent`, `shopping_agent`, and `price_extractor_agent` are implemented and integrated.
    *   **Tools:** BrightData integration (`search_tools_bd.py`) is active.
*   **Missing Components:**
    *   **State:** The system is currently stateless. It forgets the user and context between requests.
    *   **Local Market:** No integration with local used-goods marketplaces (Tori.fi).

## 3. Proposed Solution / Refactoring Strategy

### 3.1. High-Level Design
The architecture remains **Hub-and-Spoke**. The existing Orchestrator will be enhanced to consult a **Memory Service** before delegating tasks to the existing Agents.

### 3.2. Detailed Action Plan / Phases

#### Phase 3: Memory & State Foundation (High Priority)
*   **Objective:** Implement persistence ("Long-term memory") and context ("Session memory").
*   **Task 3.1: Infrastructure & Configuration**
    *   **Rationale:** Required for database connectivity.
    *   **Deliverable:** Updated `config.py` and `pyproject.toml` with `google-cloud-firestore` and caching dependencies.
*   **Task 3.2: Firestore Service (Long-Term Memory)**
    *   **Rationale:** Store user profiles, past searches, and preferences across sessions.
    *   **Deliverable:** `app/services/firestore.py` implementing `get_profile(user_id)` and `save_interaction(user_id, data)`.
*   **Task 3.3: Session Service (Short-Term Memory)**
    *   **Rationale:** Maintain context within a conversation (e.g., "Show me more results" refers to the previous search).
    *   **Deliverable:** `app/memory/session_service.py` (In-Memory implementation).
*   **Task 3.4: Orchestrator Integration**
    *   **Rationale:** The Orchestrator must read memory to personalize the prompt and write memory to save state.
    *   **Deliverable:** Update `app/subagents/orchestrator/agent.py` to inject memory context into the system instructions.

#### Phase 4: Local Market Specialist (Tori.fi) (Low Priority / Deferred)
*   **Objective:** Expand search capabilities to the local used market.
*   **Status:** **Deferred**. Functionality is needed but resources are currently unavailable.
*   **Task 4.1: Local Scraper Service**
    *   **Rationale:** Need a custom scraper for Tori.fi as it requires specific parsing logic.
    *   **Deliverable:** `app/services/tori_scraper.py`.
*   **Task 4.2: Local Search Agent**
    *   **Rationale:** A specialized agent to handle "used" or "local" queries, distinct from the global shopping agent.
    *   **Deliverable:** `app/subagents/local_search/agent.py`.
*   **Task 4.3: Orchestrator Routing Update**
    *   **Rationale:** Logic to decide when to route to Local Search vs. Global Shopping (or both).
    *   **Deliverable:** Updated `root_agent` instructions to handle the new sub-agent.

#### Phase 5: System Refinement & Optimization (Ongoing)
*   **Objective:** Maintain and improve the currently implemented agents (Research, Shopping, Orchestrator).
*   **Status:** **Partially Implemented / Ongoing**.
*   **Task 5.1: Error Handling & Resilience**
    *   **Rationale:** The `price_extractor` and `shopping_agent` rely on external APIs (BrightData). Robust error handling is crucial.
    *   **Deliverable:** Enhanced retry logic and fallback mechanisms in `app/subagents/shopping/agent.py`.
*   **Task 5.2: Performance Tuning**
    *   **Rationale:** Parallel execution of `price_extractor` agents can be resource-intensive.
    *   **Deliverable:** Optimization of concurrency limits in `deploy.py` or agent configurations.

## 4. Key Considerations & Risk Mitigation

### 4.1. Technical Risks
*   **Memory Latency:** Adding Firestore lookups to every request increases latency.
    *   *Mitigation:* Implement aggressive caching (TTL) for user profiles in `app/services/firestore.py`.
*   **Cost Management:** Firestore reads/writes cost money.
    *   *Mitigation:* Design the schema to minimize read operations (e.g., fetch one "Profile" document per session start).

### 4.2. Dependencies
*   **Phase 3:** Depends on Google Cloud Firestore API enablement and Service Account permissions.
*   **Phase 4:** Independent of Phase 3, but requires development time not currently allocated.

## 5. Success Metrics
1.  **Memory:** The bot recognizes a returning user and references past context (e.g., "Welcome back, looking for headphones again?").
2.  **Stability:** The existing Shopping/Research agents continue to function without regression during Memory integration.

## 6. Assumptions
*   The existing `orchestrator` structure allows for easy injection of context strings into the `instruction` prompt.
*   Phase 4 can be picked up at any time without major refactoring of the core system, as it will just be another "Spoke" in the architecture.
