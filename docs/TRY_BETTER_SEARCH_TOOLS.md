# Refactoring Plan: Integrate BrightData Local MCP

## 1. Executive Summary & Goals
The objective is to replace the existing DuckDuckGo and local fetch tools in the `shopping_agent` with BrightData's Local MCP integration (`@brightdata/mcp`). This will provide enterprise-grade SERP and Crawling capabilities via a local standard input/output (Stdio) server.

**Key Goals:**
1.  **Configuration:** Securely manage the BrightData API Token.
2.  **Tool Integration:** Create `app/tools/search_tools_bd.py` to run the BrightData MCP server locally via `npx`.
3.  **Agent Refactoring:** Update the `shopping_agent` to natively use the exposed SERP and Crawler tools, leveraging their specific parameters (e.g., `country`, `search_engine`) instead of hardcoded Python logic.

## 2. Current Situation Analysis
-   **Existing:** `shopping_agent` relies on `find_shopping_links` (custom Python/DuckDuckGo) and `fetch_tool` (local `uvx`).
-   **Problem:** Search performance is poor; hardcoded query logic is brittle.
-   **Target:** Use BrightData's MCP which exposes:
    -   **Bright Data SERP Search:** For finding products with geolocation support.
    -   **Bright Data Web Crawler:** For deep extraction and price verification.

## 3. Proposed Solution / Refactoring Strategy

### 3.1. High-Level Design
The `shopping_agent` will connect to a local subprocess running `npx @brightdata/mcp`. The agent will be responsible for formulating search queries and selecting the correct tool parameters (specifically `country` and `search_engine`) based on the user's request.

### 3.2. Key Components

#### A. Configuration (`app/config.py`)
-   Add `brightdata_api_token` to the `Settings` class.

#### B. New Tool Module (`app/tools/search_tools_bd.py`)
-   Initialize `McpToolset` using `StdioConnectionParams`.
-   **Command:** `npx`
-   **Args:** `["-y", "@brightdata/mcp"]`
-   **Env:** Inject `API_TOKEN` from settings.

#### C. Shopping Agent Refactoring (`app/subagents/shopping/agent.py`)
-   **Tools:** Replace existing tools with the new `brightdata_toolset`.
-   **Instructions:** Rewrite the system prompt to utilize the specific capabilities described in the integration guide:
    -   **Search:** Use **Bright Data SERP Search**. Map user location to the `country` parameter (e.g., "fi", "us"). Use `search_engine="google"` or `"bing"`.
    -   **Verify:** Use **Bright Data Web Crawler** for the specific product URL found. Use `output_format="markdown"` or `"json"` for easy parsing.

### 3.3. Detailed Action Plan

#### Phase 1: Configuration & Tool Implementation
*   **Task 1.1: Update Settings**
    *   **File:** `app/config.py`
    *   **Action:** Add `brightdata_api_token: str` to `Settings`.
    *   **Rationale:** Secure token storage.

*   **Task 1.2: Create BrightData Tool Module**
    *   **File:** `app/tools/search_tools_bd.py`
    *   **Action:** Create file exporting `brightdata_toolset`.
    *   **Implementation:**
        *   Import `McpToolset`, `StdioConnectionParams`, `StdioServerParameters`.
        *   Configure the Stdio server with the `npx` command and `API_TOKEN` env var.
    *   **Deliverable:** A working MCP toolset instance.

#### Phase 2: Agent Integration
*   **Task 2.1: Update Shopping Agent Imports**
    *   **File:** `app/subagents/shopping/agent.py`
    *   **Action:** Import `brightdata_toolset` and remove old tool imports.

*   **Task 2.2: Refactor Shopping Agent Instructions**
    *   **File:** `app/subagents/shopping/agent.py`
    *   **Action:** Update `instruction` in `_create_shopping_agent`.
    *   **New Logic:**
        1.  **Identify Country:** Extract country code (e.g., 'us', 'de', 'fi').
        2.  **Search:** Call `serp_search` (or exact exposed name) with:
            *   `query`: "[Product Name] price buy"
            *   `country`: [Country Code]
            *   `search_engine`: "google"
        3.  **Select & Verify:** Pick the best URL and call `web_crawler` (or exact exposed name) with:
            *   `start_url`: [Selected URL]
            *   `country`: [Country Code] (for proxy geolocation)
        4.  **Extract:** Parse the crawler output for price and stock status.

## 4. Key Considerations & Risk Mitigation
### 4.1. Technical Risks
-   **Tool Naming:** The exact tool names exposed by `@brightdata/mcp` might differ slightly from the guide (e.g., `bright_data_serp_search` vs `serp`).
    -   *Mitigation:* The Agent's LLM is generally good at mapping intent to available tools, but we will explicitly mention "Bright Data SERP" in the prompt to guide it.
-   **Node.js Requirement:** The environment must have `npx` installed.

### 4.2. Dependencies
-   Valid `BRIGHTDATA_API_TOKEN`.
-   `@brightdata/mcp` package availability via `npx`.

## 5. Success Metrics
-   `shopping_agent` initializes without errors.
-   Agent successfully calls the SERP tool with the correct `country` parameter.
-   Agent successfully crawls a product page and extracts price data.

## 6. Assumptions
-   The `@brightdata/mcp` package exposes tools that align with the provided descriptions (SERP Search, Web Crawler).
-   The local environment has `npx` installed and network access to BrightData APIs.
