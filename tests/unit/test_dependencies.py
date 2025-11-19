"""
Unit tests for the dependencies module.

Tests cover dependency injection functions: get_config(), get_agent_engine(),
and get_telegram_service(), including singleton behavior and proper dependency injection.
"""

from unittest.mock import Mock, patch

import pytest

from app.config import Settings

# Import the modules to test
from app.dependencies import get_agent_engine, get_config, get_telegram_service


class TestGetConfig:
    """Test cases for the get_config() function."""

    @patch("app.dependencies.get_settings")
    def test_get_config_returns_settings_instance(
        self, mock_get_settings: Mock
    ) -> None:
        """Test that get_config() returns a Settings instance."""
        # Mock the get_settings function to return a Settings instance
        mock_settings = Mock(spec=Settings)
        mock_get_settings.return_value = mock_settings

        # Call get_config()
        result = get_config()

        # Verify it returns the Settings instance from get_settings()
        assert result is mock_settings
        mock_get_settings.assert_called_once()

    @patch("app.dependencies.get_settings")
    def test_get_config_singleton_behavior(self, mock_get_settings: Mock) -> None:
        """Test that get_config() returns the same instance on multiple calls (singleton behavior)."""
        # Mock the get_settings function
        mock_settings = Mock(spec=Settings)
        mock_get_settings.return_value = mock_settings

        # Call get_config() multiple times
        result1 = get_config()
        result2 = get_config()
        result3 = get_config()

        # All results should be the same instance due to @lru_cache in get_settings()
        assert result1 is result2
        assert result2 is result3
        assert result1 is result3

        # get_settings should be called multiple times but return cached instance
        assert mock_get_settings.call_count >= 1

    @patch("app.dependencies.get_settings")
    def test_get_config_delegates_to_get_settings(
        self, mock_get_settings: Mock
    ) -> None:
        """Test that get_config() properly delegates to get_settings()."""
        # Create a mock Settings instance
        mock_settings = Mock(spec=Settings)
        mock_settings.gcp_project_id = "test-project"
        mock_settings.telegram_bot_token = "test-token"
        mock_get_settings.return_value = mock_settings

        # Call get_config()
        result = get_config()

        # Verify get_settings was called
        mock_get_settings.assert_called_once()

        # Verify the result is the expected Settings instance
        assert isinstance(result, Settings)
        assert result.gcp_project_id == "test-project"
        assert result.telegram_bot_token == "test-token"


class TestGetAgentEngine:
    """Test cases for the get_agent_engine() function."""

    def test_get_agent_engine_returns_agent_engine_instance(self) -> None:
        """Test that get_agent_engine() returns the agent engine instance."""
        # This test uses the actual agent_engine instance since it's a module-level singleton
        # We just verify that the function returns the expected type and it's the same instance
        result = get_agent_engine()

        # Verify it returns an instance (should be the actual AgentEngineApp)
        from app.agent_engine_app import AgentEngineApp

        assert isinstance(result, AgentEngineApp)

        # Verify it's the same instance when called multiple times (singleton behavior)
        result2 = get_agent_engine()
        assert result is result2

    def test_get_agent_engine_singleton_behavior(self) -> None:
        """Test that get_agent_engine() returns the same instance on multiple calls (singleton)."""
        # Call get_agent_engine() multiple times
        result1 = get_agent_engine()
        result2 = get_agent_engine()
        result3 = get_agent_engine()

        # All results should be the same instance (module-level singleton)
        assert result1 is result2
        assert result2 is result3
        assert result1 is result3


class TestGetTelegramService:
    """Test cases for the get_telegram_service() function."""

    @patch("app.dependencies.TelegramService")
    @patch("app.dependencies.get_config")
    @patch("app.dependencies.get_agent_engine")
    def test_get_telegram_service_creates_service_with_dependencies(
        self,
        mock_get_agent_engine: Mock,
        mock_get_config: Mock,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test that get_telegram_service() creates TelegramService with proper dependencies."""
        # Set up mocks
        mock_config = Mock(spec=Settings)
        mock_config.telegram_bot_token = "test-bot-token-123"
        mock_get_config.return_value = mock_config

        mock_engine = Mock()
        mock_get_agent_engine.return_value = mock_engine

        mock_service_instance = Mock()
        mock_telegram_service_class.return_value = mock_service_instance

        # Call get_telegram_service()
        result = get_telegram_service()

        # Verify dependencies were obtained
        mock_get_config.assert_called_once()
        mock_get_agent_engine.assert_called_once()

        # Verify TelegramService was instantiated with correct arguments
        mock_telegram_service_class.assert_called_once_with(
            bot_token="test-bot-token-123", agent_engine=mock_engine
        )

        # Verify the result is the TelegramService instance
        assert result is mock_service_instance

    @patch("app.dependencies.TelegramService")
    @patch("app.dependencies.get_config")
    @patch("app.dependencies.get_agent_engine")
    def test_get_telegram_service_injects_config_and_agent_engine(
        self,
        mock_get_agent_engine: Mock,
        mock_get_config: Mock,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test that get_telegram_service() properly injects config and agent_engine."""
        # Set up mocks with specific values
        mock_config = Mock(spec=Settings)
        mock_config.telegram_bot_token = "injection-test-token"
        mock_get_config.return_value = mock_config

        mock_engine = Mock()
        mock_engine.__class__.__name__ = "AgentEngineApp"
        mock_get_agent_engine.return_value = mock_engine

        mock_service_instance = Mock()
        mock_telegram_service_class.return_value = mock_service_instance

        # Call get_telegram_service()
        result = get_telegram_service()

        # Verify the service was created with the correct dependencies
        mock_telegram_service_class.assert_called_once_with(
            bot_token="injection-test-token", agent_engine=mock_engine
        )

        # Verify the result
        assert isinstance(result, Mock)

    @patch("app.dependencies.TelegramService")
    @patch("app.dependencies.get_config")
    @patch("app.dependencies.get_agent_engine")
    def test_get_telegram_service_dependency_order(
        self,
        mock_get_agent_engine: Mock,
        mock_get_config: Mock,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test that get_telegram_service() calls dependencies in the correct order."""
        # Set up mocks
        mock_config = Mock(spec=Settings)
        mock_config.telegram_bot_token = "order-test-token"
        mock_get_config.return_value = mock_config

        mock_engine = Mock()
        mock_get_agent_engine.return_value = mock_engine

        mock_service_instance = Mock()
        mock_telegram_service_class.return_value = mock_service_instance

        # Track call order
        call_order = []

        def track_config_call() -> Mock:
            call_order.append("get_config")
            return mock_config

        def track_engine_call() -> Mock:
            call_order.append("get_agent_engine")
            return mock_engine

        mock_get_config.side_effect = track_config_call
        mock_get_agent_engine.side_effect = track_engine_call

        # Call get_telegram_service()
        get_telegram_service()

        # Verify dependencies were called in the correct order
        assert "get_config" in call_order
        assert "get_agent_engine" in call_order
        assert call_order.index("get_config") < call_order.index("get_agent_engine")

    @patch("app.dependencies.TelegramService")
    @patch("app.dependencies.get_config")
    @patch("app.dependencies.get_agent_engine")
    def test_get_telegram_service_with_none_bot_token(
        self,
        mock_get_agent_engine: Mock,
        mock_get_config: Mock,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test get_telegram_service() behavior when bot token is None."""
        # Set up mocks with None bot token
        mock_config = Mock(spec=Settings)
        mock_config.telegram_bot_token = None
        mock_get_config.return_value = mock_config

        mock_engine = Mock()
        mock_get_agent_engine.return_value = mock_engine

        mock_service_instance = Mock()
        mock_telegram_service_class.return_value = mock_service_instance

        # Call get_telegram_service()
        result = get_telegram_service()

        # Verify TelegramService was called with None bot token
        mock_telegram_service_class.assert_called_once_with(
            bot_token=None, agent_engine=mock_engine
        )

        assert result is mock_service_instance


class TestDependenciesIntegration:
    """Integration tests for dependencies module behavior."""

    @patch("app.dependencies.TelegramService")
    def test_all_dependencies_work_together(
        self,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test that all dependency functions work together correctly."""
        # Set up mocks for TelegramService
        mock_service = Mock()
        mock_telegram_service_class.return_value = mock_service

        # Call all dependency functions
        config = get_config()
        engine = get_agent_engine()
        service = get_telegram_service()

        # Verify all functions work correctly
        assert isinstance(config, Settings)

        from app.agent_engine_app import AgentEngineApp

        assert isinstance(engine, AgentEngineApp)

        assert service is mock_service

        # Verify TelegramService was called with correct arguments
        mock_telegram_service_class.assert_called_once_with(
            bot_token=config.telegram_bot_token, agent_engine=engine
        )

    @patch("app.dependencies.get_settings")
    def test_dependencies_preserve_types(
        self,
        mock_get_settings: Mock,
    ) -> None:
        """Test that dependency functions preserve correct types."""
        # Set up mocks
        mock_settings = Mock(spec=Settings)
        mock_get_settings.return_value = mock_settings

        # Call dependency functions
        config = get_config()
        engine = get_agent_engine()

        # Verify types are preserved
        assert isinstance(config, Settings)
        assert config is mock_settings

        from app.agent_engine_app import AgentEngineApp

        assert isinstance(engine, AgentEngineApp)


class TestDependenciesErrorHandling:
    """Test cases for error handling in dependencies module."""

    @patch("app.dependencies.get_settings")
    def test_get_config_raises_exception_from_get_settings(
        self, mock_get_settings: Mock
    ) -> None:
        """Test that get_config() properly propagates exceptions from get_settings()."""
        # Mock get_settings to raise an exception
        mock_get_settings.side_effect = Exception("Settings loading failed")

        # Call get_config() and expect the exception to propagate
        with pytest.raises(Exception, match="Settings loading failed"):
            get_config()

        mock_get_settings.assert_called_once()

    @patch("app.dependencies.TelegramService")
    @patch("app.dependencies.get_config")
    @patch("app.dependencies.get_agent_engine")
    def test_get_telegram_service_raises_exception_from_dependencies(
        self,
        mock_get_agent_engine: Mock,
        mock_get_config: Mock,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test that get_telegram_service() properly propagates exceptions from dependencies."""
        # Mock get_config to raise an exception
        mock_get_config.side_effect = Exception("Config loading failed")

        # Call get_telegram_service() and expect the exception to propagate
        with pytest.raises(Exception, match="Config loading failed"):
            get_telegram_service()

        mock_get_config.assert_called_once()
        mock_get_agent_engine.assert_not_called()
        mock_telegram_service_class.assert_not_called()

    @patch("app.dependencies.TelegramService")
    @patch("app.dependencies.get_config")
    @patch("app.dependencies.get_agent_engine")
    def test_get_telegram_service_raises_exception_from_telegram_service_creation(
        self,
        mock_get_agent_engine: Mock,
        mock_get_config: Mock,
        mock_telegram_service_class: Mock,
    ) -> None:
        """Test that get_telegram_service() properly propagates exceptions from TelegramService."""
        # Set up mocks to work until TelegramService creation
        mock_config = Mock(spec=Settings)
        mock_config.telegram_bot_token = "test-token"
        mock_get_config.return_value = mock_config

        mock_engine = Mock()
        mock_get_agent_engine.return_value = mock_engine

        # Mock TelegramService constructor to raise an exception
        mock_telegram_service_class.side_effect = Exception(
            "TelegramService creation failed"
        )

        # Call get_telegram_service() and expect the exception to propagate
        with pytest.raises(Exception, match="TelegramService creation failed"):
            get_telegram_service()

        # Verify all dependencies were called before the exception
        mock_get_config.assert_called_once()
        mock_get_agent_engine.assert_called_once()
        mock_telegram_service_class.assert_called_once()
