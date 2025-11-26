"""
BrightData Local MCP integration module.

This module provides integration with BrightData's Local MCP server (@brightdata/mcp)
for enterprise-grade SERP and web crawling capabilities.
"""

from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp import StdioServerParameters

from app.config import get_settings


def _create_brightdata_toolset() -> McpToolset:
    """
    Create the BrightData MCP toolset using StdioConnectionParams.

    This function initializes the MCP toolset with the following configuration:
    - Command: npx
    - Args: ["-y", "@brightdata/mcp"]
    - Environment: API_TOKEN injected from settings

    Returns:
        McpToolset: Configured MCP toolset instance for BrightData services
    """
    settings = get_settings()

    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@brightdata/mcp"],
                env={
                    "API_TOKEN": settings.brightdata_api_token,
                },
            ),
            timeout=settings.brightdata_api_timeout,
        )
    )


# Global BrightData toolset instance for use by agents
brightdata_toolset = _create_brightdata_toolset()
