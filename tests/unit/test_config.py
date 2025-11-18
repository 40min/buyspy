"""
Unit tests for the config module.

Tests cover Settings class validation, environment variable handling,
and singleton behavior of get_settings() function.
"""

import os
from collections.abc import Generator
from typing import Any

import pytest
from pydantic import ValidationError

# Import the modules to test
from app.config import Settings, get_settings


def _get_env_vars_to_clear() -> list[str]:
    """
    Dynamically get environment variable names from Settings class fields.

    Returns a list of uppercase environment variable names that correspond
    to Settings fields.
    """
    # Get field names from Settings model
    field_names = Settings.model_fields.keys()

    # Convert to uppercase environment variable names
    return [field_name.upper() for field_name in field_names]


@pytest.fixture(autouse=True)
def clear_env_vars() -> Generator[None, None, None]:
    """
    Clear environment variables before each test and restore them after.

    This fixture ensures test isolation by:
    1. Forcing ENV_FILE to .env.test (never use real .env)
    2. Clearing all Settings-related environment variables
    3. Clearing the settings cache
    """
    # ALWAYS force ENV_FILE to .env.test to prevent loading real .env
    os.environ["ENV_FILE"] = ".env.test"

    # Get environment variables to clear dynamically from Settings class
    env_vars_to_clear = _get_env_vars_to_clear()

    # Clear all test-related environment variables BEFORE the test runs
    for key in env_vars_to_clear:
        if key in os.environ:
            del os.environ[key]

    # Clear the settings cache to ensure fresh settings for each test
    get_settings.cache_clear()

    yield

    # After test: Clear ALL test values that were set during the test
    for key in env_vars_to_clear:
        if key in os.environ:
            del os.environ[key]

    # ALWAYS restore ENV_FILE to .env.test (never leave it pointing to real .env)
    os.environ["ENV_FILE"] = ".env.test"

    # Clear cache again after cleanup
    get_settings.cache_clear()


class TestSettingsClass:
    """Test cases for the Settings class."""

    def test_settings_with_valid_env_vars(self) -> None:
        """Test Settings creation with valid environment variables."""
        # Set up environment variables
        os.environ["GCP_PROJECT_ID"] = "test-project-123"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-bot-token-456"
        os.environ["GCP_REGION"] = "europe-west1"
        os.environ["ARTIFACTS_BUCKET_NAME"] = "test-bucket"
        os.environ["LOG_LEVEL"] = "DEBUG"

        settings = Settings()

        assert settings.gcp_project_id == "test-project-123"
        assert settings.telegram_bot_token == "test-bot-token-456"
        assert settings.gcp_region == "europe-west1"
        assert settings.artifacts_bucket_name == "test-bucket"
        assert settings.log_level == "DEBUG"

    def test_settings_with_required_vars_only(self) -> None:
        """Test Settings creation with only required environment variables."""
        # Set only required environment variables
        os.environ["GCP_PROJECT_ID"] = "minimal-test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "minimal-token"

        settings = Settings()

        # Check required fields
        assert settings.gcp_project_id == "minimal-test-project"
        assert settings.telegram_bot_token == "minimal-token"

        # Check default values for optional fields
        assert settings.gcp_region == "europe-west1"  # default value
        assert settings.artifacts_bucket_name is None  # default value
        assert settings.log_level == "INFO"  # default value

    def test_settings_invalid_gcp_region_format(self) -> None:
        """Test Settings with invalid GCP region format."""
        os.environ["GCP_PROJECT_ID"] = "test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["GCP_REGION"] = "invalid-region-format"

        # This should still work as it's a string field
        settings = Settings()
        assert settings.gcp_region == "invalid-region-format"

    def test_settings_case_insensitive_env_vars(self) -> None:
        """Test that environment variables are case insensitive."""
        # Set environment variables in different cases (lowercase)
        os.environ["gcp_project_id"] = "lowercase-project"
        os.environ["telegram_bot_token"] = "lowercase-token"
        os.environ["gcp_region"] = "asia-southeast1"

        try:
            settings = Settings()

            assert settings.gcp_project_id == "lowercase-project"
            assert settings.telegram_bot_token == "lowercase-token"
            assert settings.gcp_region == "asia-southeast1"
        finally:
            # Clean up lowercase variants explicitly in this test
            for key in ["gcp_project_id", "telegram_bot_token", "gcp_region"]:
                if key in os.environ:
                    del os.environ[key]

    def test_settings_empty_string_values(self) -> None:
        """Test Settings with empty string values for required fields."""
        # Temporarily use a different ENV_FILE to avoid .env.test values
        os.environ["ENV_FILE"] = "/tmp/non_existent_env_file"

        # Clear any cached settings
        get_settings.cache_clear()

        os.environ["GCP_PROJECT_ID"] = ""
        os.environ["TELEGRAM_BOT_TOKEN"] = "valid-token"

        # Empty string for required field should raise ValidationError
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_optional_fields_with_empty_strings(self) -> None:
        """Test Settings with empty strings for optional fields."""
        os.environ["GCP_PROJECT_ID"] = "test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["ARTIFACTS_BUCKET_NAME"] = ""
        os.environ["LOG_LEVEL"] = ""

        settings = Settings()

        # Optional fields should accept empty strings
        assert settings.artifacts_bucket_name == ""
        assert settings.log_level == ""

    def test_settings_special_characters_in_values(self) -> None:
        """Test Settings with special characters in environment variable values."""
        os.environ["GCP_PROJECT_ID"] = "test-project-with-dashes_123"
        os.environ["TELEGRAM_BOT_TOKEN"] = (
            "1234567890:AAEhBOg2hD8vQqP8X8pQqP8X8pQqP8X8pQqP8X"
        )

        settings = Settings()

        assert settings.gcp_project_id == "test-project-with-dashes_123"
        assert (
            settings.telegram_bot_token
            == "1234567890:AAEhBOg2hD8vQqP8X8pQqP8X8pQqP8X8pQqP8X"
        )


class TestGetSettings:
    """Test cases for the get_settings() function."""

    def test_get_settings_singleton_behavior(self) -> None:
        """Test that get_settings() returns the same instance (singleton pattern)."""
        # Set up environment variables
        os.environ["GCP_PROJECT_ID"] = "singleton-test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "singleton-test-token"

        # Clear the cache to ensure fresh test
        get_settings.cache_clear()

        # Get settings multiple times
        settings1 = get_settings()
        settings2 = get_settings()
        settings3 = get_settings()

        # All should be the same instance due to @lru_cache()
        assert settings1 is settings2
        assert settings2 is settings3
        assert settings1 is settings3

    def test_get_settings_cache_clearing(self) -> None:
        """Test that clearing the cache creates a new instance."""
        # Set up environment variables
        os.environ["GCP_PROJECT_ID"] = "cache-test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "cache-test-token"

        # Clear the cache first
        get_settings.cache_clear()

        # Get initial settings
        settings1 = get_settings()

        # Clear the cache again
        get_settings.cache_clear()

        # Get settings after cache clear
        settings2 = get_settings()

        # Should be different instances
        assert settings1 is not settings2

        # But should have same values
        assert settings1.gcp_project_id == settings2.gcp_project_id
        assert settings1.telegram_bot_token == settings2.telegram_bot_token

    def test_get_settings_with_valid_env_vars(self) -> None:
        """Test get_settings() function with valid environment variables."""
        os.environ["GCP_PROJECT_ID"] = "get-settings-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "get-settings-token"
        os.environ["GCP_REGION"] = "europe-west2"

        # Clear cache to ensure fresh test
        get_settings.cache_clear()

        settings = get_settings()

        assert isinstance(settings, Settings)
        assert settings.gcp_project_id == "get-settings-project"
        assert settings.telegram_bot_token == "get-settings-token"
        assert settings.gcp_region == "europe-west2"

    def test_get_settings_preserves_default_values(self) -> None:
        """Test that get_settings() preserves default values for optional fields."""
        # Temporarily disable .env.test to test actual defaults
        os.environ["ENV_FILE"] = "/tmp/non_existent_env_file"

        os.environ["GCP_PROJECT_ID"] = "defaults-test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "defaults-test-token"

        # Clear cache to ensure fresh test
        get_settings.cache_clear()

        settings = get_settings()

        # Check default values
        assert settings.gcp_region == "europe-west1"
        assert settings.artifacts_bucket_name is None
        assert settings.log_level == "INFO"


class TestSettingsIntegration:
    """Integration tests for Settings class behavior."""

    def test_env_vars_override_dotenv_file(self, tmp_path: Any) -> None:
        """Test that environment variables take precedence over .env file."""
        # Create a .env file
        env_content = """
GCP_PROJECT_ID=env-file-project
TELEGRAM_BOT_TOKEN=env-file-token
"""
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)

        # Temporarily override the ENV_FILE to point to our test .env
        os.environ["ENV_FILE"] = str(env_file)

        # Set environment variables that should override .env file
        os.environ["GCP_PROJECT_ID"] = "env-var-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "env-var-token"

        settings = Settings()

        # Should use environment variable values, not .env file values
        assert settings.gcp_project_id == "env-var-project"
        assert settings.telegram_bot_token == "env-var-token"

    def test_settings_type_validation(self) -> None:
        """Test that Settings properly validates field types."""
        os.environ["GCP_PROJECT_ID"] = "type-test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "type-test-token"

        settings = Settings()

        # Verify types
        assert isinstance(settings.gcp_project_id, str)
        assert isinstance(settings.telegram_bot_token, str)
        assert isinstance(settings.gcp_region, str)
        assert isinstance(settings.artifacts_bucket_name, str | None)
        assert isinstance(settings.log_level, str)


class TestSettingsDefaults:
    """Test cases specifically for Settings default values."""

    def test_default_gcp_region_value(self) -> None:
        """Test that GCP_REGION has the correct default value."""
        # Temporarily disable .env.test to test actual defaults
        os.environ["ENV_FILE"] = "/tmp/non_existent_env_file"

        os.environ["GCP_PROJECT_ID"] = "test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

        # Don't set GCP_REGION, should use default
        settings = Settings()
        assert settings.gcp_region == "europe-west1"

    def test_default_log_level_value(self) -> None:
        """Test that LOG_LEVEL has the correct default value."""
        os.environ["GCP_PROJECT_ID"] = "test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

        # Don't set LOG_LEVEL, should use default
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_default_artifacts_bucket_name_value(self) -> None:
        """Test that ARTIFACTS_BUCKET_NAME has the correct default value."""
        os.environ["GCP_PROJECT_ID"] = "test-project"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

        # Don't set ARTIFACTS_BUCKET_NAME, should use default
        settings = Settings()
        assert settings.artifacts_bucket_name is None


class TestSettingsFromTestEnv:
    """Test cases that verify .env.test is being used."""

    def test_settings_uses_env_test_file(self) -> None:
        """Test that Settings loads from .env.test file when conftest sets ENV_FILE."""
        # Ensure ENV_FILE is set to .env.test
        os.environ["ENV_FILE"] = ".env.test"

        # Clear cache to force reload from .env.test
        get_settings.cache_clear()

        settings = Settings()

        # Should load values from .env.test
        assert settings.gcp_project_id == "test-project-123"
        assert settings.telegram_bot_token == "test-bot-token-456"

        # .env.test has GCP_REGION set to europe-west1
        assert settings.gcp_region == "europe-west1"
        # Optional fields not in .env.test should use defaults
        assert settings.artifacts_bucket_name is None
        assert settings.log_level == "INFO"

    def test_env_test_file_content_matches_expected(self) -> None:
        """Verify the .env.test file has the expected content."""
        # Ensure ENV_FILE is set to .env.test
        os.environ["ENV_FILE"] = ".env.test"

        # Clear cache to force reload from .env.test
        get_settings.cache_clear()

        settings = Settings()

        # These values should come from .env.test
        assert settings.gcp_project_id == "test-project-123"
        assert settings.telegram_bot_token == "test-bot-token-456"
        assert settings.gcp_region == "europe-west1"
