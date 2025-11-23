# Refactoring/Design Plan: BuySpy - Multi-Agent System Demonstration

## 1. Executive Summary & Goals
This plan transforms the BuySpy MVP into a **Multi-Agent System (MAS)** demonstration. The objective is to showcase advanced agentic patterns required for the demo‚Äîspecifically **Parallel Execution**, **Sequential Processing**, and **Hybrid Memory**‚Äîwithin the context of a personalized shopping concierge.

**Key Goals:**
1.  **Demonstrate Agent Patterns:** Implement an **Orchestrator** that manages **Parallel Agents** (simultaneous New vs. Used market search) and **Sequential Agents** (Review/Vetting).
2.  **Advanced State Management:** Integrate **Firestore** for Long-Term Memory (Memory Bank) and an **InMemorySessionService** for session state, optimized with caching.
3.  **Tooling Showcase:** Utilize **Built-in Tools** (Google Search), **Custom Tools** (Tori Scraper, Places API), and **MCP-style** interfaces.

## 2. Current Situation Analysis
*   **Current State:** Single-agent MVP (`root_agent`) in `app/agent.py`. High code quality but lacks persistence and multi-agent coordination.
*   **Gap Analysis:**
    *   **Missing Patterns:** No parallel execution or sequential delegation.
    *   **Missing State:** Stateless architecture prevents "concierge" experience.
    *   **Missing Features:** No localized search (Tori.fi) or shop vetting.
*   **Alignment:** This plan aligns with the "Multi-Agent System" requirement by restructuring the monolithic agent into a coordinated system of specialized components.

## 3. Proposed Solution / Refactoring Strategy

### 3.1. High-Level Design / Architectural Overview

We will implement a **Hub-and-Spoke Architecture**. The **Orchestrator Agent** (Hub) receives user input, interacts with the **Memory Layer**, and coordinates **Specialist Agents/Tools** (Spokes).

**Interaction Flow:**
1.  **Input:** User sends message.
2.  **Context:** Orchestrator fetches **Long-Term Memory** (Firestore) and **Session State** (InMemory).
3.  **Decision:** Orchestrator formulates a plan.
4.  **Parallel Execution:** Orchestrator triggers `WebSearchAgent` (Google) and `LocalSearchAgent` (Tori) simultaneously.
5.  **Sequential Execution:** Results are passed to the `ReviewAgent` (Places API) to vet vendors.
6.  **Loop (Optional):** If user requests "More results," Orchestrator loops back to search tools with incremented pagination (tracked in Session).
7.  **Output:** Synthesized response.

### 3.2. Directory Structure
```text
buyspy/
‚îú‚îÄ‚îÄ app/
‚îÇ   ‚îú‚îÄ‚îÄ agent.py                  # Composition Root (Entry Point)
‚îÇ   ‚îú‚îÄ‚îÄ subagents/                   # [NEW] Agent Definitions
‚îÇ   ‚îÇ   ‚îú‚îÄ‚îÄ orchestrator.py     # The "Brain"
‚îÇ   ‚îÇ   ‚îú‚îÄ‚îÄ specialists.py      # WebSearcher, LocalSearcher, Reviewer
‚îÇ   ‚îú‚îÄ‚îÄ memory/                   # [NEW] State Management
‚îÇ   ‚îÇ   ‚îú‚îÄ‚îÄ memory_bank.py      # Firestore Wrapper (Long-term)
‚îÇ   ‚îÇ   ‚îî‚îÄ‚îÄ session_service.py  # In-Memory Service (Short-term)
‚îÇ   ‚îú‚îÄ‚îÄ services/                 # [NEW] Raw I/O & API Wrappers
‚îÇ   ‚îÇ   ‚îú‚îÄ‚îÄ firestore.py        # DB Client + Caching
‚îÇ   ‚îÇ   ‚îú‚îÄ‚îÄ tori_scraper.py     # HTML Parsing
‚îÇ   ‚îÇ   ‚îî‚îÄ‚îÄ google_services.py  # Translation, Places, Search
‚îÇ   ‚îú‚îÄ‚îÄ tools/                    # [NEW] Tool Interfaces (MCP-style)
‚îÇ   ‚îÇ   ‚îú‚îÄ‚îÄ search_tools.py     # ToriTool, GoogleSearchTool
‚îÇ   ‚îÇ   ‚îî‚îÄ‚îÄ context_tools.py    # MemoryTool
...
```

### 3.3. Detailed Action Plan / Phases

#### Phase 3: Memory & State Foundation
*   **Objective:** Implement "Sessions & Memory" and "Long term memory".
*   **Task 3.1: Infrastructure Setup**
    *   **Priority:** High
    *   **Action:** Add `google-cloud-firestore`, `cachetools` to `pyproject.toml`. Update `config.py`.
*   **Task 3.2: Firestore Service (Long-Term)**
    *   **Priority:** High
    *   **Action:** Create `app/services/firestore.py`. Implement `get_profile(user_id)` with TTL caching to minimize costs.
*   **Task 3.3: InMemorySessionService (Session)**
    *   **Priority:** High
    *   **Action:** Create `app/memory/session_service.py`.
    *   **Logic:** Simple dictionary storage for `current_step`, `pagination_index`, `last_query`.

#### Phase 4: The Specialists (Tools & Services)
*   **Objective:** Implement "Custom tools" and "Built-in tools".
*   **Task 4.1: Local Search Service (Tori.fi)**
    *   **Priority:** High
    *   **Action:** Create `app/services/tori_scraper.py` (Scraping) and `app/services/google_services.py` (Translation).
*   **Task 4.2: Tool Wrappers**
    *   **Priority:** High
    *   **Action:** Create `app/tools/search_tools.py`.
    *   **Tools:**
        *   `ToriTool`: Handles "Search Both" (English + Translated).
        *   `PlacesTool`: Wraps Google Places API for shop ratings.

#### Phase 5: Multi-Agent Orchestration
*   **Objective:** Demo "Parallel agents", "Sequential agents", and "Loop agents" (Pagination).
*   **Task 5.1: Specialist Definitions**
    *   **Priority:** Medium
    *   **Action:** Create `app/agents/specialists.py`.
    *   **Logic:** Define lightweight classes or callables that encapsulate the prompt/tool config for:
        *   `WebSearchSpecialist`: Focused on new items (Google Search).
        *   `LocalSearchSpecialist`: Focused on used items (Tori).
        *   `ReviewSpecialist`: Focused on vetting.
*   **Task 5.2: Orchestrator Implementation**
    *   **Priority:** Critical
    *   **Action:** Create `app/agents/orchestrator.py`.
    *   **Logic:**
        *   **Context:** `await memory.get_context()`
        *   **Parallel:** `await asyncio.gather(web_specialist.run(), local_specialist.run())`
        *   **Sequential:** Pass results to `review_specialist.run()`.
        *   **Loop:** If user says "Next page", update Session `page_index` and re-run search.
*   **Task 5.3: Entry Point Refactoring**
    *   **Priority:** Critical
    *   **Action:** Update `app/agent.py` to instantiate the Orchestrator. Ensure `make playground` works by exporting the `app` object correctly.

## 4. Key Considerations & Risk Mitigation

### 4.1. Technical Risks
*   **Complexity vs. Latency:** Orchestrating multiple agents increases latency.
    *   *Mitigation:* Use `asyncio.gather` for parallel searches. Provide immediate feedback ("Searching markets...") via Telegram.
*   **Session Persistence:** In-memory sessions die on restart.
    *   *Mitigation:* Acceptable for "Session" scope. "Long-term" data in Firestore persists.

### 4.2. Dependencies
*   `google-cloud-firestore`
*   `cachetools`
*   `beautifulsoup4`
*   `httpx` (for async scraping)

### 4.3. Non-Functional Requirements
*   **Observability:** Trace the parallel execution path in Google Cloud Trace to prove parallelism.
*   **Cost:** Caching is strictly implemented for Firestore reads.

## 5. Success Metrics / Validation Criteria
1.  **Pattern Verification:** Logs confirm that `ToriSearch` and `GoogleSearch` start at the same timestamp (Parallelism).
2.  **Memory Verification:** User restarts bot -> Bot remembers name (Long-term) but resets pagination (Session).
3.  **Feature Verification:** Searching for "Bike" returns used options from Tori.fi and new options from Google.

## 6. Assumptions
*   The "Loop" pattern will be demonstrated via a "Next Page" / Pagination workflow, which is natural for shopping.
*   We will simulate distinct "Agents" via modular code organization within the single ADK runtime.

## 7. Open Questions
*   **None.** The path to a demo-ready Multi-Agent System is clear.
