"""
BrightData Streamable HTTP MCP integration module.

This module provides integration with BrightData's Streamable HTTP MCP server
for enterprise-grade SERP and web crawling capabilities.
"""

from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from app.config import get_settings


def _create_brightdata_toolset() -> McpToolset:
    """
    Create the BrightData MCP toolset using StreamableHTTPConnectionParams.

    This function initializes the MCP toolset with the following configuration:
    - URL: https://mcp.brightdata.com/mcp
    - Authentication: API token passed via query parameter

    Returns:
        McpToolset: Configured MCP toolset instance for BrightData services
    """
    settings = get_settings()

    # Construct URL with token as query parameter
    url = f"https://mcp.brightdata.com/mcp?token={settings.brightdata_api_token}"

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            timeout=settings.brightdata_api_timeout,
        )
    )


# Global BrightData toolset instance for use by agents
brightdata_toolset = _create_brightdata_toolset()
