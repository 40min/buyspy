"""
Pytest configuration file for setting up test environment.

This file is loaded before any test modules and sets up the test environment
to use .env.test instead of .env for testing.
"""

import os
from collections.abc import Generator

import pytest

# Set test environment file BEFORE any imports that could trigger config loading
os.environ["ENV_FILE"] = ".env.test"


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Set up test environment variables"""
    test_env = {
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "GOOGLE_CLOUD_LOCATION": "europe-north1",
        "GOOGLE_GENAI_USE_VERTEXAI": "True",
        "ARTIFACTS_BUCKET_NAME": "test-bucket",
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_env

    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
