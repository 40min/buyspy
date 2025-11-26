from unittest.mock import Mock, patch

import pytest

from app.subagents.price_extractor.agent import price_extractor_agent


@pytest.fixture
def mock_google_auth() -> Mock:
    """Mock Google authentication for tests."""
    with patch("google.auth.default") as mock_auth:
        mock_auth.return_value = (None, "test-project")
        yield mock_auth


def test_price_extractor_agent_is_instance_of_agent(mock_google_auth: Mock) -> None:
    """Test that price_extractor_agent is an instance of Agent."""
    from google.adk.agents import Agent

    assert isinstance(price_extractor_agent, Agent)


def test_price_extractor_agent_model(mock_google_auth: Mock) -> None:
    """Test that price_extractor_agent uses the correct model."""
    assert price_extractor_agent.model == "gemini-2.5-flash-lite"


def test_price_extractor_agent_tools(mock_google_auth: Mock) -> None:
    """Test that price_extractor_agent has brightdata_toolset in tools."""
    from app.tools.search_tools_bd import brightdata_toolset

    assert brightdata_toolset in price_extractor_agent.tools
