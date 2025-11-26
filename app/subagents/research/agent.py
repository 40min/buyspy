from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.adk.tools.google_search_tool import google_search
from google.genai.types import GenerateContentConfig


def _create_research_agent(current_year: str) -> Agent:
    return Agent(
        name="research_agent",
        model="gemini-2.5-flash-lite",
        tools=[google_search],
        generate_content_config=GenerateContentConfig(
            temperature=0.1,
        ),
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


# Global research agent instance
research_agent = _create_research_agent(current_year="2025")

app = App(
    root_agent=research_agent,
    name="research",
    plugins=[
        ReflectAndRetryToolPlugin(max_retries=10),
    ],
)
