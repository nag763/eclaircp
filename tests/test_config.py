"""
Tests for the configuration module.
"""

import pytest
from pydantic import ValidationError
from eclaircp.config import MCPServerConfig, SessionConfig, ConfigFile


def test_mcp_server_config_validation():
    """Test MCPServerConfig validation."""
    config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"],
        description="Test server"
    )
    assert config.name == "test-server"
    assert config.command == "uvx"
    assert config.args == ["test-package"]


def test_mcp_server_config_empty_command():
    """Test that empty command raises validation error."""
    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="test-server",
            command="",
            args=["test-package"]
        )


def test_session_config_validation():
    """Test SessionConfig validation."""
    config = SessionConfig(server_name="test-server")
    assert config.server_name == "test-server"
    assert config.model == "us.anthropic.claude-3-7-sonnet-20250219-v1:0"


def test_config_file_validation():
    """Test ConfigFile validation."""
    server_config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"]
    )
    config_file = ConfigFile(servers={"test": server_config})
    assert "test" in config_file.servers