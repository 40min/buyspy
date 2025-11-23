import datetime
import os

import google.auth
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools import AgentTool

from ..research.agent import research_agent
from ..shopping.agent import shopping_agent


def _initialize_google_auth() -> str:
    """Initialize Google Auth and return the project ID."""
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return project_id


def _create_root_agent() -> Agent:
    _initialize_google_auth()
    """Create the root agent that coordinates the subagents."""
    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.datetime.now().strftime("%Y")

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
  1. Call `research_agent` with the following input: "Research [User Query] for [Country Name]"
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


# Global root agent instance
root_agent = _create_root_agent()

app = App(root_agent=root_agent, name="orchestrator")
