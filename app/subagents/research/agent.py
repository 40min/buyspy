from datetime import datetime

from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.tools.google_search_tool import google_search
from google.genai.types import GenerateContentConfig

from app.subagents.config import default_retry_config


def _create_research_agent(current_year: str) -> Agent:
    return Agent(
        name="research_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=default_retry_config),
        tools=[google_search],
        generate_content_config=GenerateContentConfig(
            temperature=0.1,
        ),
        instruction=f"""You are a Regional Product Research Specialist.

**Input:** "Research [Category] for [Country Name]"

Use {current_year} as default year if not specified.

### YOUR JOB
1. Search for "Best [Category] [Country Name] [Year]"
2. Find 1-5 top recommended models
3. Reasoning: For each model, identify the *key reason* it is recommended (e.g., "Best Value", "Best Battery Life", "Top Tier Audio").

### OUTPUT
Return ONLY valid JSON (no extra text):

```json
[
  {{
    "model": "Exact Model Name",
    "reason": "Why it's recommended"
  }}
]
```

Example:
```json
[
  {{
    "model": "iPhone 15 Pro",
    "reason": "Best overall performance and camera",
  }},
  {{
    "model": "Samsung Galaxy S24",
    "reason": "Best value flagship",
  }}
]
```
""",
    )


# Global research agent instance
research_agent = _create_research_agent(current_year=str(datetime.now().year))

app = App(
    root_agent=research_agent,
    name="research",
)
