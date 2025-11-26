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

from app.agent import root_agent


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
    assert root_agent.name == "root_agent"


def test_agent_model(mock_google_auth: Mock) -> None:
    """Test that the agent uses the correct model."""
    assert root_agent.model == "gemini-2.5-flash-lite"
