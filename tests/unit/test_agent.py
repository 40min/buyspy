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

from unittest.mock import Mock, patch

import pytest

from app.agent import get_root_agent


@pytest.fixture
def mock_google_auth() -> Mock:
    """Mock Google authentication for tests."""
    with patch("app.agent.google.auth.default") as mock_auth:
        mock_auth.return_value = (None, "test-project")
        yield mock_auth


@pytest.fixture
def mock_google_search_tool() -> Mock:
    """Mock Google Search tool to avoid actual API calls."""
    with patch("app.agent.GoogleSearchTool") as mock_tool:
        yield mock_tool


def test_agent_name(mock_google_auth: Mock) -> None:
    """Test that the agent has the correct name."""
    agent = get_root_agent()
    assert agent.name == "root_agent"


def test_agent_model(mock_google_auth: Mock) -> None:
    """Test that the agent uses the correct model."""
    agent = get_root_agent()
    assert agent.model == "gemini-2.5-flash-lite"


def test_agent_instruction_is_shopping_assistant(mock_google_auth: Mock) -> None:
    """Test that the agent instruction is configured as a shopping assistant."""
    agent = get_root_agent()
    instruction = agent.instruction

    # Check that the instruction contains shopping-related keywords
    assert isinstance(instruction, str)
    assert "BuySpy" in instruction
    assert "shopping assistant" in instruction.lower()
    assert "purchasing decisions" in instruction.lower()
    assert "Google Search" in instruction
    assert "products" in instruction.lower()
    assert "reviews" in instruction.lower()


def test_agent_has_google_search_tool(
    mock_google_auth: Mock, mock_google_search_tool: Mock
) -> None:
    """Test that the agent is equipped with Google Search tool."""
    agent = get_root_agent()
    tools = agent.tools

    assert len(tools) == 1
    assert any("GoogleSearchTool" in str(tool) for tool in tools)


def test_agent_instruction_mentions_search_capabilities(mock_google_auth: Mock) -> None:
    """Test that the agent instruction mentions web search capabilities."""
    agent = get_root_agent()
    instruction = agent.instruction

    assert isinstance(instruction, str)
    assert "Search for product information" in instruction
    assert "web search" in instruction.lower()
    assert "real-time information" in instruction.lower()


def test_agent_instruction_mentions_helpful_approach(mock_google_auth: Mock) -> None:
    """Test that the agent instruction emphasizes helpful and unbiased approach."""
    agent = get_root_agent()
    instruction = agent.instruction

    assert isinstance(instruction, str)
    assert "helpful" in instruction.lower()
    assert "polite" in instruction.lower()
    assert "unbiased" in instruction.lower()
    assert "balanced" in instruction.lower()


def test_agent_instruction_mentions_comparison_capabilities(
    mock_google_auth: Mock,
) -> None:
    """Test that the agent instruction mentions comparison and analysis capabilities."""
    agent = get_root_agent()
    instruction = agent.instruction

    assert isinstance(instruction, str)
    assert "Compare products" in instruction
    assert "detailed analysis" in instruction.lower()
    assert "alternatives" in instruction.lower()
