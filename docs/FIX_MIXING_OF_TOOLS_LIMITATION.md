# Guide: Building BuySpy with Multi-Agent Architecture

## 1. Problem Definition
**The Error:** `400 INVALID_ARGUMENT: Multiple tools are supported only when they are all search tools.`
**The Cause:** You cannot mix the native Google Grounding tool (`google_search`) with custom Python functions in a single agent.
**The Solution:**
1.  Create a **Sub-Agent** dedicated solely to Google Search (Grounding).
2.  Create a **Root Agent** that has access to the Sub-Agent (via `AgentTool`) AND your custom Shopping Tool (`duckduckgo`).
3.  The Root Agent orchestrates the workflow: Ask Sub-Agent for ideas -> Use Custom Tool for links.

---

## 2. Implementation

### Step 1: Dependencies & Custom Tool
First, define the custom tool that finds the raw links using DuckDuckGo.

```python
from duckduckgo_search import DDGS
from google.adk.model import Agent, Model, Gemini
from google.adk.tools import AgentTool
from google.adk.tools.google_search_tool import google_search
import json

# --- Custom Tool: The Shopper ---
def find_shopping_links(product_name: str, region: str):
    """
    Finds direct shop links and prices for a SPECIFIC product in a specific region.
    
    Args:
        product_name: The specific model name (e.g. "Sony WH-CH720N").
        region: The region code (e.g. "fi-fi", "us-en").
    """
    query = f"{product_name} price"
    # We return JSON so the Root Agent can read it easily
    try:
        results = DDGS().text(query, region=region, max_results=3)
        return json.dumps(results)
    except Exception as e:
        return f"Error finding links: {str(e)}"
```

### Step 2: The Research Sub-Agent
This agent has **one job**: Use Google Grounding to answer general questions. It does not need to know about shopping links.

```python
# --- Sub-Agent: The Researcher ---
research_agent = Agent(
    name="research_agent",
    # Use your preferred model version here
    model="gemini-1.5-flash-002", 
    instruction="""You are a Research Specialist.
    Your goal is to find high-quality information using Google Search.
    
    - When asked about products, summarize the best options, pros, and cons.
    - Be concise and factual.
    - DO NOT worry about finding direct shop links; just identify the best products.
    """,
    tools=[google_search] # Native Grounding Tool
)
```

### Step 3: The Root Agent (Orchestrator)
This agent controls the flow. It treats `research_agent` as a tool to get information, and `find_shopping_links` as a tool to get URLs.

```python
# --- Root Agent: The Orchestrator ---
root_agent = Agent(
    name="root_agent",
    model="gemini-1.5-flash-002",
    
    # It has access to the Sub-Agent AND the Python Function
    tools=[AgentTool(agent=research_agent), find_shopping_links],
    
    instruction="""You are BuySpy, an advanced shopping assistant.

    ### YOUR WORKFLOW
    You must orchestrate a multi-step process to help the user.

    **STEP 1: DETERMINE REGION**
    - Check if the user stated their location/country.
    - **IF UNKNOWN:** You MUST ask: "Which country are you shopping in?" and stop.
    - **IF KNOWN:** Convert to a region code (e.g., Finland -> 'fi-fi').

    **STEP 2: RESEARCH (Using 'research_agent')**
    - If the user asks "What is the best...", call the `research_agent`.
    - Ask the research_agent to recommend specific product models based on the user's needs.
    - *Example Tool Input:* "Best noise cancelling headphones under 100 euros 2024"

    **STEP 3: ACQUISITION (Using 'find_shopping_links')**
    - Take the specific model names returned by the `research_agent`.
    - Call `find_shopping_links` for each model using the region code from Step 1.
    - *Example Tool Input:* product_name="Sony WH-CH720N", region="fi-fi"

    **STEP 4: SYNTHESIS**
    - Combine the findings.
    - List the product, why it's good (from research), the best price found, and the DIRECT LINK (from shopping tool).
    """
)

return root_agent
```

---

## 3. How It Works

This architecture is robust because it separates concerns:

1.  **User:** "What are the best headphones for gym in Finland?"
2.  **Root Agent:**
    *   *Detects Region:* Finland (`fi-fi`).
    *   *Needs Info:* Calls `AgentTool(research_agent)` with prompt: "Best gym headphones 2024".
3.  **Research Agent:**
    *   Calls `google_search` (Grounding).
    *   Returns: "Jabra Elite 8 Active and Jaybird Vista 2 are best."
4.  **Root Agent:**
    *   *Receives info.* Now needs prices.
    *   Calls `find_shopping_links("Jabra Elite 8 Active", "fi-fi")`.
    *   Calls `find_shopping_links("Jaybird Vista 2", "fi-fi")`.
5.  **Root Agent:**
    *   Synthesizes the final response with clickable links from DuckDuckGo.

## 4. Summary of Benefits

*   **API Compliant:** Solves the `400 INVALID_ARGUMENT` error.
*   **High Quality:** Uses Google's superior understanding for research (via Grounding) and DuckDuckGo's raw access for URL retrieval.
*   **Modular:** If you want to change how research is done, you only edit the Sub-Agent. If you want to change how links are found, you only edit the Python function.