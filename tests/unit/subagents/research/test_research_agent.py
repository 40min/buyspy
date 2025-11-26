from unittest.mock import Mock, patch

import pytest

from app.subagents.research.agent import research_agent


@pytest.fixture
def mock_google_auth() -> Mock:
    """Mock Google authentication for tests."""
    with patch("google.auth.default") as mock_auth:
        mock_auth.return_value = (None, "test-project")
        yield mock_auth


def test_research_agent_is_instance_of_agent(mock_google_auth: Mock) -> None:
    """Test that research_agent is an instance of Agent."""
    from google.adk.agents import Agent

    assert isinstance(research_agent, Agent)


def test_research_agent_model(mock_google_auth: Mock) -> None:
    """Test that research_agent uses the correct model."""
    assert research_agent.model == "gemini-2.5-flash-lite"


def test_research_agent_tools(mock_google_auth: Mock) -> None:
    """Test that research_agent has google_search in tools."""
    from google.adk.tools.google_search_tool import google_search

    assert google_search in research_agent.tools
