from unittest.mock import Mock, patch

import pytest

from app.subagents.shopping.agent import shopping_agent


@pytest.fixture
def mock_google_auth() -> Mock:
    """Mock Google authentication for tests."""
    with patch("google.auth.default") as mock_auth:
        mock_auth.return_value = (None, "test-project")
        yield mock_auth


def test_shopping_agent_is_instance_of_agent(mock_google_auth: Mock) -> None:
    """Test that shopping_agent is an instance of Agent."""
    from google.adk.agents import Agent

    assert isinstance(shopping_agent, Agent)


def test_shopping_agent_model(mock_google_auth: Mock) -> None:
    """Test that shopping_agent uses the correct model."""
    assert shopping_agent.model == "gemini-2.5-flash"


def test_shopping_agent_tools(mock_google_auth: Mock) -> None:
    """Test that shopping_agent has brightdata_toolset and price_extractor_agent (as AgentTool) in tools."""
    from google.adk.tools import AgentTool

    from app.subagents.price_extractor.agent import price_extractor_agent
    from app.tools.search_tools_bd import brightdata_toolset

    assert brightdata_toolset in shopping_agent.tools
    # Check that there's an AgentTool wrapping price_extractor_agent
    agent_tools = [t for t in shopping_agent.tools if isinstance(t, AgentTool)]
    assert len(agent_tools) == 1
    assert agent_tools[0].agent == price_extractor_agent
