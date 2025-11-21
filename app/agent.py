# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools.google_search_tool import google_search

from app.tools.link_finder import find_shopping_links


def _initialize_google_auth() -> str:
    """Initialize Google Auth and return the project ID."""
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return project_id


def _create_root_agent() -> Agent:
    """Create the root agent with lazy initialization."""
    _initialize_google_auth()
    return Agent(
        name="root_agent",
        model="gemini-2.5-flash-lite",
        tools=[google_search, find_shopping_links],
        instruction="""You are BuySpy, an intelligent shopping assistant.

    ### YOUR WORKFLOW (Follow strictly)

    **STEP 1: CHECK REGION**
    - Before finding any prices or links, you MUST know the user's region.
    - Check the conversation history. Did the user mention a country (Finland, US, UK)?
    - **IF REGION IS UNKNOWN:** Stop and ask: "Which country are you shopping in?"
    - **IF REGION IS KNOWN:** Map it to a code (Finland -> 'fi-fi', USA -> 'us-en', UK -> 'uk-en', Germany -> 'de-de')

    **STEP 2: RESEARCH (The "What")**
    - If the user asks generic questions (e.g., "Best headphones?"), use `google_search`.
    - Summarize the best options, pros/cons, and select specific models to recommend.

    **STEP 3: SHOPPING (The "Where")**
    - Once you have specific model names AND the region code, use the `find_shopping_links` tool.
    - Call this tool for EACH recommended product individually.
    - **CRITICAL:** Extract the 'href' (URL) exactly as provided by the tool. Do not guess URLs.

    ### RESPONSE FORMAT
    When recommending products, use this structure:

    **[Product Name]**
    *   **Why it's good:** [Summary from Step 2]
    *   **Best Price:** [Price from Step 3] at [Store Name from Step 3]
    *   **Link:** [Direct URL from Step 3]
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
