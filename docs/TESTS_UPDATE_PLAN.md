# Refactoring Plan: Test Suite Cleanup & Consolidation

## 1. Executive Summary & Goals
The primary objective of this plan is to align the project's test suite with the "Test Behavior, Not Implementation" philosophy by removing brittle configuration tests and consolidating duplicate test logic.

**Key Goals:**
1.  **Eliminate Brittle Tests:** Remove tests that assert on class composition, configuration, and private state (specifically for Agents and Tools).
2.  **Consolidate & Organize:** Clean up duplicate test files and ensure the test directory structure strictly mirrors the application source tree.

## 2. Current Situation Analysis
*   **Agent Tests:** The files in `tests/unit/subagents/` (e.g., `test_agent.py`, `test_shopping_agent.py`) purely verify that classes are instantiated with specific models or tools. This violates the "Don't test class composition" rule.
*   **Tool Tests:** `tests/unit/tools/test_search_tools_bd.py` inspects private attributes (`_connection_params`) to verify configuration, violating the "Don't assert on internal methods or private state" rule.
*   **Duplicate Testing:** Markdown escaping logic is tested in two places: `tests/unit/app_utils/test_telegram_markdown.py` (correct location) and `tests/unit/services/test_markdown_escaping.py` (incorrect location).
*   **Scaffolding Code:** `app/app_utils/gcs.py` and `app/app_utils/tracing.py` are generated scaffolding code and are excluded from unit testing scope.

## 3. Proposed Solution / Refactoring Strategy

### 3.1. High-Level Design
The strategy involves a "Prune and Consolidate" approach:
1.  **Prune:** Delete tests that validate declarative configuration (Agents, Tools).
2.  **Consolidate:** Merge duplicate tests into the correct directory structure.

### 3.2. Detailed Action Plan / Phases

#### **Phase 1: Cleanup & Pruning (High Priority)**
*Objective: Remove tests that violate the "Test Behavior" principle to reduce maintenance burden.*

*   **Task 1.1: Remove Agent Configuration Tests**
    *   **Action:** Delete the entire `tests/unit/subagents/` directory.
    *   **Rationale:** These tests check `isinstance`, `agent.model`, and `agent.tools`. As per user rules ("Probably tests for agents are not needed"), these are unnecessary configuration checks.
    *   **Deliverable:** Files deleted.

*   **Task 1.2: Remove Tool Internal State Tests**
    *   **Action:** Delete `tests/unit/tools/test_search_tools_bd.py`.
    *   **Rationale:** This test mocks `get_settings` and asserts on `toolset._connection_params` (private state).
    *   **Deliverable:** File deleted.

#### **Phase 2: Consolidation (Medium Priority)**
*Objective: Ensure existing tests follow the correct hierarchy.*

*   **Task 2.1: Consolidate Markdown Tests**
    *   **Action:** Move unique test cases from `tests/unit/services/test_markdown_escaping.py` to `tests/unit/app_utils/test_telegram_markdown.py`, then delete the source file.
    *   **Rationale:** `test_markdown_escaping.py` tests a utility function residing in `app_utils`, so the test belongs in `tests/unit/app_utils`.
    *   **Deliverable:** Single, comprehensive test file in the correct location.

## 4. Key Considerations & Risk Mitigation

### 4.1. Technical Risks
*   **None:** This plan involves removing and moving tests, not altering application logic.

### 4.2. Dependencies
*   None.

### 4.3. Non-Functional Requirements
*   **Maintainability:** Removing configuration tests significantly reduces the burden when changing models or prompts.
*   **Organization:** Aligning test structure with source structure improves discoverability.

## 5. Success Metrics
*   **Reduction in Test Count:** Total number of tests will decrease, but the *value* per test increases.
*   **Zero Configuration Tests:** No tests fail simply because a model name changed.
*   **Clean Hierarchy:** Every test file exists in a folder structure mirroring the `app/` directory.

## 6. Assumptions
*   The `deploy.py` script is a CLI tool and is adequately covered by manual testing or deployment pipelines.
*   The "Agents" are primarily declarative (prompts + tool definitions) and do not contain custom Python logic requiring unit tests.
*   Scaffolded utilities (`gcs.py`, `tracing.py`) are trusted code.

## 7. Open Questions
*   None.
