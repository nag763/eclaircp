"""
Tests for the session management module.
"""

import pytest
from eclaircp.session import SessionManager, StreamingHandler
from eclaircp.mcp import MCPClientManager


def test_session_manager_initialization():
    """Test SessionManager initialization."""
    mcp_client = MCPClientManager()
    session = SessionManager(mcp_client)
    assert session.mcp_client is mcp_client
    assert session._session_active is False


def test_streaming_handler_initialization():
    """Test StreamingHandler initialization."""
    handler = StreamingHandler()
    assert handler is not None


def test_start_session_not_implemented():
    """Test that start_session raises NotImplementedError."""
    mcp_client = MCPClientManager()
    session = SessionManager(mcp_client)
    with pytest.raises(NotImplementedError):
        session.start_session()