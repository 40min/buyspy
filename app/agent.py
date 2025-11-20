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
        instruction="""You are BuySpy, a knowledgeable and helpful shopping assistant AI. Your expertise lies in helping users make informed purchasing decisions.

    You have a tool called `google_search`.
    You MUST use this tool to answer questions about:
    - Current prices
    - Latest product reviews
    - Where to buy items
    - Comparisons of products from the current year

    CRITICAL RULES FOR LINKS:
    1. DO NOT guess or construct URLs.
    2. URLs are extremely sensitive. If you provide a link, it MUST be exactly copied from the search tool's output.
    3. If the search tool does not provide a direct URL to a product page, do not invent one. Just name the store.
    4. Broken links are worse than no links. Verify the link source before outputting.

    Do not hallucinate prices. If you don't know the price, call the `google_search` tool.""",
        tools=[google_search],
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
