"""
Unit tests for BrightData search tools module.

Tests the initialization and configuration of the BrightData MCP toolset,
focusing on proper dependency injection and parameter passing.
"""

from unittest.mock import MagicMock, patch

from app.config import Settings
from app.tools.search_tools_bd import _create_brightdata_toolset, brightdata_toolset


class TestBrightDataToolset:
    """Test suite for BrightData toolset initialization and configuration."""

    @patch("app.tools.search_tools_bd.get_settings")
    def test_brightdata_toolset_initialization(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that brightdata_toolset is properly initialized with mocked settings."""
        # Create mock settings with dummy API token
        mock_settings = MagicMock(spec=Settings)
        mock_settings.brightdata_api_token = "test_dummy_api_token"
        mock_get_settings.return_value = mock_settings

        # Create a fresh toolset instance (since global one might already be initialized)
        toolset = _create_brightdata_toolset()

        # Verify get_settings was called
        mock_get_settings.assert_called_once()

        # Verify toolset is created and has expected type
        assert toolset is not None
        # Verify the toolset has the expected private attributes
        assert hasattr(toolset, "_connection_params")

    @patch("app.tools.search_tools_bd.get_settings")
    def test_mcp_connection_parameters_contain_api_token(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that MCP connection parameters contain the API token in environment."""
        # Create mock settings with specific API token
        expected_token = "brightdata_test_token_123"
        mock_settings = MagicMock(spec=Settings)
        mock_settings.brightdata_api_token = expected_token
        mock_get_settings.return_value = mock_settings

        # Create toolset instance
        toolset = _create_brightdata_toolset()

        # Access connection params safely
        conn_params = toolset._connection_params
        server_params = conn_params.server_params

        # Verify connection parameters contain the API token
        assert isinstance(server_params.env, dict)
        assert server_params.env["API_TOKEN"] == expected_token

        # Verify other expected parameters
        assert server_params.command == "npx"
        assert server_params.args == ["-y", "@brightdata/mcp"]
        assert conn_params.timeout == 60

    @patch("app.tools.search_tools_bd.get_settings")
    def test_brightdata_toolset_handles_empty_token(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that toolset creation handles edge cases like empty tokens."""
        # Test with empty token
        mock_settings = MagicMock(spec=Settings)
        mock_settings.brightdata_api_token = ""
        mock_get_settings.return_value = mock_settings

        toolset = _create_brightdata_toolset()

        # Should still create toolset even with empty token
        assert toolset is not None
        conn_params = toolset._connection_params
        server_params = conn_params.server_params
        assert isinstance(server_params.env, dict)
        assert server_params.env["API_TOKEN"] == ""

    def test_global_brightdata_toolset_exists(self) -> None:
        """Test that the global brightdata_toolset instance exists."""
        # This tests the global instance (may be initialized with real settings)
        assert brightdata_toolset is not None
        assert hasattr(brightdata_toolset, "_connection_params")
