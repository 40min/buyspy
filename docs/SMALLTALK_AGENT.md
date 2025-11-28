# Refactoring/Design Plan: Add Smalltalk Agent

## 1. Executive Summary & Goals
-   **Objective:** Integrate a new "Smalltalk" agent into the existing multi-agent architecture to handle general conversation and general research queries, distinct from the existing product-focused agents.
-   **Goals:**
    1.  Create a new subagent (`smalltalk`) capable of Google Search and witty conversation.
    2.  Update the Orchestrator to recognize non-shopping intents and delegate them to the new agent.
    3.  Maintain the existing shopping workflows without regression.

## 2. Current Situation Analysis
-   **Architecture:** The system uses a central `orchestrator` agent that delegates to `research` (product recommendations) and `shopping` (price extraction).
-   **Limitation:** The current orchestrator system prompt is rigidly defined for a shopping workflow ("Step 1: Detect Country", etc.), making it difficult to handle casual chat or general questions.
-   **Solution:** Introduce a third branch of execution for general intents handled by a dedicated agent.

## 3. Proposed Solution / Refactoring Strategy

### 3.1. High-Level Design
The Orchestrator will act as a router.
-   **Input:** User Message.
-   **Router Logic (LLM Decision):**
    -   *Shopping/Product Intent* -> Existing Flow (Country Detect -> Research/Shopping).
    -   *General Intent* -> Delegate to `smalltalk_agent`.

### 3.2. Key Components
1.  **`app.subagents.smalltalk.agent` (New):**
    -   A Gemini-based agent.
    -   Tools: `google_search`.
    -   Persona: Funny, witty, helpful for general queries.
2.  **`app.subagents.orchestrator.agent` (Modified):**
    -   Updated system prompt to include the new agent and routing logic.
    -   Updated tool list.

### 3.3. Detailed Action Plan

-   **Phase 1: Create Smalltalk Agent**
    -   **Task 1.1:** Create directory `app/subagents/smalltalk`.
    -   **Task 1.2:** Create `app/subagents/smalltalk/__init__.py` (empty).
    -   **Task 1.3:** Create `app/subagents/smalltalk/agent.py`.
        -   **Goal:** Define the agent with `google_search` tool and a "funny guy" persona.
        -   **Deliverable:** A functional agent module exporting `smalltalk_agent`.

-   **Phase 2: Update Orchestrator**
    -   **Task 2.1:** Modify `app/subagents/orchestrator/agent.py`.
        -   **Import:** Import `smalltalk_agent` from the new module.
        -   **Tools:** Add `AgentTool(smalltalk_agent)` to the `root_agent` tools list.
        -   **Prompt Engineering:** Rewrite the `instruction` string.
            -   Add `smalltalk_agent` to the "AVAILABLE AGENTS" list description.
            -   Modify "YOUR WORKFLOW" to handle the branching logic (Shopping vs. General).
            -   Ensure the "funny" persona is emphasized for the general path.

## 4. Key Considerations & Risk Mitigation
### 4.1. Technical Risks
-   **Ambiguity:** The LLM might struggle to distinguish between "Research headphones" (Product) and "Research the history of headphones" (General).
    -   *Mitigation:* Explicitly define `research_agent` as "Product/Shopping Research" and `smalltalk_agent` as "General Knowledge/Chat" in the orchestrator's prompt.

### 4.2. Dependencies
-   `google.adk.tools.google_search_tool` (Existing dependency).

### 4.3. NFRs
-   **Maintainability:** The new agent follows the existing pattern (separate folder, `agent.py`, `__init__.py`), ensuring consistency.

## 5. Success Metrics
-   User can ask "What is the capital of Finland?" and get a witty answer (via `smalltalk_agent`).
-   User can ask "Best headphones in Finland" and get the standard shopping response (via `research_agent`/`shopping_agent`).

## 6. Assumptions
-   The `google_search` tool is correctly configured in the environment (as it is already used by `research_agent`).
-   The `default_retry_config` is available in `app.subagents.config`.

## 7. Open Questions
-   None.
