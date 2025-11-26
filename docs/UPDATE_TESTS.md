# Refactoring Plan: Comprehensive Test Coverage for Modular Agents

## 1. Executive Summary & Goals
- **Objective:** Establish a robust unit testing suite for the recently refactored modular agent architecture (`app/subagents/*`) and utility modules.
- **Goals:**
  1.  Align test file structure with the new source code structure (moving `test_agent.py`).
  2.  Implement missing unit tests for `price_extractor`, `research`, and `shopping` subagents.
  3.  Verify behavior of tools, utilities (`gcs`, `tracing`), and dependency injection.
  4.  Ensure all tests adhere to strict "behavior-based" testing rules (input -> expected output/state).

## 2. Current Situation Analysis
- **Refactoring Status:** The application has been successfully refactored into submodules (`app/subagents/`).
- **Test Gap:**
  - Existing tests (`tests/unit/test_agent.py`) target the `root_agent` but are located in the root unit folder, violating the "follow path structure" rule.
  - No tests exist for the new subagents (`price_extractor`, `research`, `shopping`).
  - No tests exist for `app/tools/search_tools_bd.py`.
  - No tests exist for `app/app_utils` (`gcs.py`, `tracing.py`).
  - No tests exist for `app/dependencies.py`.
- **Code Quality:** The refactored code is clean, but the lack of tests for the new modules creates a risk of regression during future changes.

## 3. Proposed Solution / Refactoring Strategy

### 3.1. High-Level Design
The testing strategy focuses on **Configuration Verification** for agents (verifying they are equipped with the correct tools and models) and **Behavior Verification** for utilities (verifying side effects like GCS calls or correct return values).

### 3.2. Detailed Action Plan / Phases

#### Phase 1: Structure Alignment
*   **Objective:** Align existing tests with the new file structure.
*   **Priority:** High
*   **Task 1.1: Move and Rename Root Agent Test**
    *   **Source:** `tests/unit/test_agent.py`
    *   **Destination:** `tests/unit/subagents/orchestrator/test_agent.py`
    *   **Rationale:** Matches `app/subagents/orchestrator/agent.py`.
    *   **Action:** Move file. Update imports in the test to point to `app.subagents.orchestrator.agent`.

#### Phase 2: Subagent Unit Tests
*   **Objective:** Verify the configuration and initialization behavior of the specialized agents.
*   **Priority:** High
*   **Task 2.1: Test Price Extractor Agent**
    *   **File:** `tests/unit/subagents/price_extractor/test_agent.py`
    *   **Target:** `app/subagents/price_extractor/agent.py`
    *   **Test Criteria:**
        - Verify `price_extractor_agent` is an instance of `Agent`.
        - Verify `model` is set to `gemini-2.5-flash-lite`.
        - Verify `tools` list contains `brightdata_toolset` (or equivalent scraping tools).
        - **Do not** test the instruction text.

*   **Task 2.2: Test Research Agent**
    *   **File:** `tests/unit/subagents/research/test_agent.py`
    *   **Target:** `app/subagents/research/agent.py`
    *   **Test Criteria:**
        - Verify `research_agent` is an instance of `Agent`.
        - Verify `model` is set to `gemini-2.5-flash-lite`.
        - Verify `tools` list contains `google_search`.

*   **Task 2.3: Test Shopping Agent**
    *   **File:** `tests/unit/subagents/shopping/test_agent.py`
    *   **Target:** `app/subagents/shopping/agent.py`
    *   **Test Criteria:**
        - Verify `shopping_agent` is an instance of `Agent`.
        - Verify `model` is set to `gemini-2.5-flash`.
        - Verify `tools` list includes `brightdata_toolset` and the `price_extractor_agent` (as a tool).

#### Phase 3: Tools & Dependencies Tests
*   **Objective:** Verify the wiring of external tools and dependency injection.
*   **Priority:** Medium
*   **Task 3.1: Test BrightData Tools**
    *   **File:** `tests/unit/tools/test_search_tools_bd.py`
    *   **Target:** `app/tools/search_tools_bd.py`
    *   **Test Criteria:**
        - Mock `get_settings` to return a dummy API token.
        - Verify `brightdata_toolset` is initialized.
        - Verify the underlying MCP connection parameters contain the mocked API token in `env`.

*   **Task 3.2: Test Dependencies**
    *   **File:** `tests/unit/test_dependencies.py`
    *   **Target:** `app/dependencies.py`
    *   **Test Criteria:**
        - Verify `get_config()` returns a `Settings` instance.
        - Verify `get_agent_engine()` returns the same instance on multiple calls (Singleton behavior).
        - Verify `get_telegram_service()` returns a valid service instance with the correct token injected.

#### Phase 4: Utility Tests
*   **Objective:** Verify helper logic and side effects.
*   **Priority:** Medium
*   **Task 4.1: Test GCS Utils**
    *   **File:** `tests/unit/app_utils/test_gcs.py`
    *   **Target:** `app/app_utils/gcs.py`
    *   **Test Criteria:**
        - Test `create_bucket_if_not_exists`:
            - Case A: Bucket exists (Mock `storage_client.get_bucket` success). Verify `create_bucket` is **not** called.
            - Case B: Bucket missing (Mock `storage_client.get_bucket` raises `NotFound`). Verify `create_bucket` **is** called.

*   **Task 4.2: Test Tracing Utils**
    *   **File:** `tests/unit/app_utils/test_tracing.py`
    *   **Target:** `app/app_utils/tracing.py`
    *   **Test Criteria:**
        - Test `CloudTraceLoggingSpanExporter.export`:
            - Verify it logs to `logging_client`.
            - Verify it calls `super().export`.
        - Test `_process_large_attributes`:
            - Case A: Small payload (<250KB). Verify no GCS upload.
            - Case B: Large payload (>250KB). Verify `store_in_gcs` is called and attributes are replaced with URI.

## 4. Key Considerations & Risk Mitigation

### 4.1. Technical Risks
-   **Mocking Complexity:** `tracing.py` interacts with OpenTelemetry classes which can be complex to mock.
    -   *Mitigation:* Mock only the public interface methods (`export`) and the Google Cloud clients (`logging_client`, `storage_client`). Do not try to mock internal OTel logic.
-   **Environment Variables:** Tests relying on `get_settings` must ensure the environment is clean.
    -   *Mitigation:* Use the existing `clear_env_vars` fixture or `mock_env_vars` to ensure isolation.

### 4.2. Dependencies
-   Tests depend on `pytest`, `unittest.mock`.
-   Tests for `tracing.py` depend on `opentelemetry-sdk`.

### 4.3. Non-Functional Requirements
-   **Maintainability:** By splitting tests into the same structure as the source code, developers can easily find where to add tests for new features.
-   **Performance:** All new tests are unit tests using mocks (no network calls), ensuring the test suite remains fast.

## 5. Success Metrics / Validation Criteria
-   **Coverage:** Every file in `app/subagents/` has a corresponding test file in `tests/unit/subagents/`.
-   **Pass Rate:** All new tests pass (`pytest` returns exit code 0).
-   **Structure:** `tree tests/unit` mirrors `tree app` (excluding `__init__.py` files where not needed).

## 6. Assumptions Made
-   The `tests/unit/conftest.py` exists or can be created if shared fixtures are needed (though we will prefer local fixtures or `tests/conftest.py` to avoid clutter).
-   The `Agent` class in `google.adk.agents` exposes `name`, `model`, and `tools` as public attributes.
