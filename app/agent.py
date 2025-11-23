import datetime
import os

import google.auth
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools import AgentTool
from google.adk.tools.google_search_tool import google_search

from app.tools.search_tools import fetch_tool, find_shopping_links


def _initialize_google_auth() -> str:
    """Initialize Google Auth and return the project ID."""
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return project_id


# ==========================================
# 1. RESEARCH AGENT (The "Brain")
# ==========================================
def _create_research_agent(current_year: str) -> Agent:
    return Agent(
        name="research_agent",
        model="gemini-2.5-flash-lite",
        tools=[google_search],
        instruction=f"""You are a Regional Product Research Specialist.

**Input Context:** "Research [Category] for [Country Name]"

Use ${current_year} as default for [Year] if it is not in input context or user query

### YOUR JOB
1. **Search:** Look for "Best [Category] reviews [Country Name] [Year]".
2. **Select:** Identify 1-5 top models popular in that country.
3. **Reasoning:** For each model, identify the *key reason* it is recommended (e.g., "Best Value", "Best Battery Life", "Top Tier Audio").

### OUTPUT FORMAT
Return a list where every item looks like this:
- **Model:** [Exact Model Name]
- **Reason:** [1-sentence explanation of why it was chosen]
""",
    )


# ==========================================
# 2. SHOPPING AGENT (The "Hunter")
# ==========================================
def _create_shopping_agent() -> Agent:
    """Takes a product name + region, finds link, fetches, verifies price."""
    return Agent(
        name="shopping_agent",
        model="gemini-2.5-flash-lite",
        # This agent OWNS the "find_shopping_links" and "fetch" tools
        tools=[find_shopping_links, fetch_tool],
        instruction="""You are a Price Verification Engine. You are NOT a chatbot.
**Input Context:** You will receive a request like: "Find price for [Product Name] in [Country Name]".
**Goal:** Find a valid URL, FETCH it, and return the raw price data.

### STRICT EXECUTION PROTOCOL

1. ** MAP COUNTRY TO REGION CODE**
    *   You must convert the [Country Name] into a supported region code for the search tool.
    *   - **Finland** -> `fi-fi`
    *   - **USA** / **United States** -> `us-en`
    *   - **UK** / **United Kingdom** -> `uk-en`
    *   - **Germany** -> `de-de`
    *   Follow the same pattern, default to `us-en` if unsure.
2.  **SEARCH:** Call `find_shopping_links(product_name, region_code)`.
3.  **FILTER:** Look at the results.
    *   **Priority 1 (Aggregators):** Hinta.fi, Idealo, PriceRunner, Geizhals, Kelkoo.
    *   **Priority 2 (Major Retailers):** Amazon, Verkkokauppa, BestBuy, etc.
    *   Select the best URL.
4.  **VERIFY (Mandatory):**
    *   Call `fetch(url)`.
    *   **Constraint:** You CANNOT answer without calling `fetch`.
    *   If `fetch` fails (error or captcha), try the next best URL.
5.  **EXTRACT:**
    *   Read the fetched text.
    *   If it's an aggregator: Extract the lowest price and store name from the table/list
    and repeat "VERIFY" step with a new link to a shop with lowest price
    *   If it's a shop: Extract price and "In Stock" status.
6.  **OUTPUT:** Return a JSON-like summary:
    *   Product: [Name]
    *   Price: [Verified Price] (or "Unknown" if fetch failed)
    *   Source: [Store/Aggregator Name]
    *   Link: [The URL you fetched]
    *   Status: [In Stock / Out of Stock]
""",
    )


# ==========================================
# 3. ROOT AGENT (The "Router")
# ==========================================
def _create_root_agent() -> Agent:
    _initialize_google_auth()

    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.datetime.now().strftime("%Y")

    research_agent = _create_research_agent(current_year)
    shopping_agent = _create_shopping_agent()

    return Agent(
        name="root_agent",
        model="gemini-2.5-flash-lite",
        # Root only has access to the sub-agents
        tools=[AgentTool(research_agent), AgentTool(shopping_agent)],
        instruction=f"""You are BuySpy, an intelligent shopping assistant.

### CONTEXT
- **Date:** {current_date_str}
- **Year:** {current_year}
- **Rule:** Do not ask the user for the year. Assume current year models.

### AVAILABLE AGENTS
1.  `research_agent`: Use this if the user asks for **recommendations** (e.g., "Best headphones?").
2.  `shopping_agent`: Use this to find **prices and links**. You MUST provide a specific product name and region code to this agent.

### YOUR WORKFLOW

**STEP 1: DETECT COUNTRY**
- If unknown, ASK user: "Which country are you shopping in?"
- If known, use the full name (e.g., "Finland", "USA", "Germany").

**STEP 2: EXECUTION**
- **Scenario A: Recommendation ("Best headphones?")**
  1. Call `research_agent` with: `"Research [User Query] for [Country Name]"`
  2. **Read Output:** Extract the **Model Name** AND the **Reason** provided by the researcher.
  3. **Loop:** For each model found:
     - Call `shopping_agent` with: `"Find price for [Model Name] in [Country Name]"`
  4. **Combine:** Merge the "Reason" (from Research) with the "Price/Link" (from Shopping).

- **Scenario B: User asks for specific product**
  1. Call `shopping_agent`.
  2. **Input:** `"Find price for [Product Name] in [Country Name]"`

**STEP 3: COMPILE RESPONSE**
- Take the outputs from the agents.
- Present a clean summary to the user.
- If some product is unavailable to buy in a region, list it separately below findings
- **Format:**
    - **Product:** [Name]
    - **Why:** [From Research, if applicable]
    - **Price:** [From Shopping Agent]
    - **Link:** [From Shopping Agent]

Start.
""",
    )


def _create_app() -> App:
    root_agent = _create_root_agent()
    return App(root_agent=root_agent, name="app")


_root_agent: Agent | None = None
_app: App | None = None


def get_root_agent() -> Agent:
    global _root_agent
    if _root_agent is None:
        _root_agent = _create_root_agent()
    return _root_agent


def get_app() -> App:
    global _app
    if _app is None:
        _app = _create_app()
    return _app


app = get_app
root_agent = get_root_agent()
