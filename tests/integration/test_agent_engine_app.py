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

# mypy: disable-error-code="arg-type"

from unittest.mock import MagicMock, patch

import pytest

from app.agent_engine_app import AgentEngineApp


@pytest.fixture
def agent_app(
    mock_env_vars: dict[str, str],
) -> AgentEngineApp:
    """Fixture to create AgentEngineApp instance with Google APIs mocked"""
    # Mock only the specific slow Google API calls as requested
    with (
        patch("app.agent_engine_app.google.auth.default") as mock_auth,
        patch("app.agent_engine_app.vertexai.init") as mock_vertexai,
    ):
        # Setup mocks for the specific calls mentioned
        mock_auth.return_value = (None, "test-project")
        mock_vertexai.return_value = None

        # Create a working AgentEngineApp instance
        agent_app = AgentEngineApp.__new__(AgentEngineApp)
        agent_app.logger = MagicMock()

        return agent_app


def test_agent_feedback(agent_app: AgentEngineApp) -> None:
    """
    Integration test for the agent feedback functionality.
    Tests that feedback can be registered successfully.
    """
    feedback_data = {
        "score": 5,
        "text": "Great response!",
        "invocation_id": "test-run-123",
    }

    # Test that register_feedback method exists and can be called
    assert hasattr(agent_app, "register_feedback")
    assert callable(agent_app.register_feedback)

    # Test that the method accepts feedback data without raising exceptions
    # This tests the integration between test setup and the method
    try:
        agent_app.register_feedback(feedback_data)
    except Exception as e:
        pytest.fail(f"register_feedback raised an exception: {e}")
