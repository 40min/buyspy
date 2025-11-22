import datetime
import os

import google.auth
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools import AgentTool
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp import StdioServerParameters

from app.tools.link_finder import find_shopping_links


def _initialize_google_auth() -> str:
    """Initialize Google Auth and return the project ID."""
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return project_id


def _get_fetch_tool() -> McpToolset:
    # Create the Fetch Tool using the native ADK integration
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uvx",  # Use 'uvx' to run the python server
                args=[
                    "mcp-server-fetch"  # The official Fetch MCP server package
                ],
                # Optional: explicitly whitelist the tool name
                tool_filter=["fetch"],
            ),
            timeout=60,  # Give it enough time to load heavy webpages
        )
    )


def _create_research_agent() -> Agent:
    """Create the research sub-agent with Google Search capabilities only."""
    return Agent(
        name="research_agent",
        model="gemini-2.5-flash-lite",
        tools=[google_search],
        instruction="""You are a Research Specialist.
Your goal is to find high-quality information using Google Search (use tool called `google_search`)

- When asked about products, summarize the best options, pros, and cons.
- Be concise and factual.
- DO NOT worry about finding direct shop links; just identify the best products.
- Current prices
- Latest product reviews
- Where to buy items
- Comparisons of products from the current year

Do not hallucinate prices. If you don't know the price, call the `google_search` tool.,
""",
    )


def _create_root_agent() -> Agent:
    """Create the root agent with lazy initialization."""
    _initialize_google_auth()

    # Create the research sub-agent
    research_agent = _create_research_agent()

    fetch_tool = _get_fetch_tool()

    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    return Agent(
        name="root_agent",
        model="gemini-2.5-flash-lite",
        # It has access to the Sub-Agent AND the Python Function
        tools=[AgentTool(agent=research_agent), find_shopping_links, fetch_tool],
        instruction=f"""You are BuySpy, an intelligent shopping assistant.

### YOUR WORKFLOW (Follow strictly)

**STEP 1: CHECK REGION**
- Before finding any prices or links, you MUST know the user's region.
- Check the conversation history. Did the user mention a country (Finland, US, UK)?
- **IF REGION IS UNKNOWN:** Stop and ask: "Which country are you shopping in?"
- **IF REGION IS KNOWN:** Map it to a code (Finland -> 'fi-fi', USA -> 'us-en', UK -> 'uk-en', Germany -> 'de-de')

**STEP 2: RESEARCH (The "What")**
- If the user asks generic questions (e.g., "Best headphones?"), use the `research_agent`.
- Ask the research_agent to recommend specific product models based on the user's needs.
- *Example Tool Input:* "Best noise cancelling headphones under 100 euros 2024"
- **CRITICAL:** When searching, ALWAYS include the year "{current_date_str}" in your query to avoid old models.

**STEP 3: SHOPPING (The "Where")**
- Once you have specific model names AND the region code, use the `find_shopping_links` tool.
- Call this tool for EACH recommended product individually.
- *Example Tool Input:* product_name="Sony WH-CH720N", region="fi-fi"
- **IMPORTANT:** The tool returns raw search results.
- **Analyze the JSON result:**
    - Look at ALL items in the list.
    - You must look at the 'body' and 'title' of the JSON results.
    - Compare the prices mentioned in the 'body' text.
    - **Ignore:** Ads, irrelevant blogs or results that look like forums, news, or developer documentation.

**STEP 4: VERIFY (use fetch_tool):**
    - Select the best link from Step 3.
    - **Use the `fetch` tool** (provided via MCP) to visit the URL.
    - Read the markdown content returned.
    - Confirm the price and "In Stock" status.
    - If the link from (Step 3) was to site-agregator, comparing prices, get the best prices and reuse
    fetch_tool to verify price and availability, use this info to clarify price and link for product to purchase

**STEP 5: REPORTING (Be Honest)**
    - Combine the findings.
    - List the product, why it's good (from research), the best price found, and the DIRECT LINK (from shopping tool).
    - **Price:** (Extract value from the search snippet, e.g., "59€". State "approx." if unsure. Do not claim it is the
    "Best Price" unless you compared multiple sources)
    - **Link:** (The exact 'href' from the tool)

### RESPONSE FORMAT
When recommending products, use this structure:

- **Product:** [Name]
- **Why:** [Summary]
- **Estimated Price:** [Price found in snippet]
- **Source:** [Store Name or Comparison Site]
- **Link:** [The 'href' URL]
""",
    )


def _create_app() -> App:
    """Create the app with lazy initialization."""
    root_agent = _create_root_agent()
    return App(root_agent=root_agent, name="app")


# Lazy-loaded instances
_root_agent: Agent | None = None
_app: App | None = None


def get_root_agent() -> Agent:
    """Get the lazy-loaded root agent."""
    global _root_agent
    if _root_agent is None:
        _root_agent = _create_root_agent()
    return _root_agent


def get_app() -> App:
    """Get the lazy-loaded app."""
    global _app
    if _app is None:
        _app = _create_app()
    return _app


# Keep backwards compatibility for existing code that expect this as a module-level variable
app = get_app
root_agent = get_root_agent()
