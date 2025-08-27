"""
Tests for the MCP client module.
"""

import pytest
from eclaircp.mcp import MCPClientManager, MCPToolProxy
from eclaircp.config import MCPServerConfig


def test_mcp_client_manager_initialization():
    """Test MCPClientManager initialization."""
    manager = MCPClientManager()
    assert manager._connected_server is None
    assert manager._connection_status is False


def test_mcp_tool_proxy_initialization():
    """Test MCPToolProxy initialization."""
    manager = MCPClientManager()
    proxy = MCPToolProxy(manager)
    assert proxy.mcp_client is manager


def test_connect_not_implemented():
    """Test that connect method raises NotImplementedError."""
    manager = MCPClientManager()
    config = MCPServerConfig(
        name="test",
        command="uvx",
        args=["test-package"]
    )
    with pytest.raises(NotImplementedError):
        manager.connect(config)