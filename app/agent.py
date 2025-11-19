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

import datetime
import os
from zoneinfo import ZoneInfo

import google.auth
from google.adk.agents import Agent
from google.adk.apps.app import App


def _initialize_google_auth() -> str:
    """Initialize Google Auth and return the project ID."""
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return project_id


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get current time information for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def _create_root_agent() -> Agent:
    """Create the root agent with lazy initialization."""
    _initialize_google_auth()
    return Agent(
        name="root_agent",
        model="gemini-2.5-flash-lite",
        instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
        tools=[get_weather, get_current_time],
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
