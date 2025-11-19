# mypy: disable-error-code="arg-type"

from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_google_apis() -> dict[str, Any]:
    """Mock only the slow external Google API calls, but allow AgentEngineApp creation"""
    with (
        patch("google.auth.default") as mock_auth,
        patch("vertexai.init") as mock_vertexai,
    ):
        # Setup mocks for the specific Google API calls
        mock_auth.return_value = (None, "test-project")
        mock_vertexai.return_value = None

        yield {
            "auth": mock_auth,
            "vertexai": mock_vertexai,
        }
