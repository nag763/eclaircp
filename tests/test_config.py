"""
Tests for the configuration module.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from eclaircp.config import (
    MCPServerConfig, SessionConfig, ConfigFile,
    ConnectionStatus, StreamEvent, StreamEventType, ToolInfo
)


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


def test_config_file_empty_servers():
    """Test that empty servers dict raises validation error."""
    with pytest.raises(ValidationError):
        ConfigFile(servers={})


def test_mcp_server_config_args_whitespace():
    """Test that args with whitespace are properly cleaned."""
    config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["  test-package  ", "", "  another-arg  "]
    )
    assert config.args == ["test-package", "another-arg"]


def test_mcp_server_config_defaults():
    """Test MCPServerConfig default values."""
    config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"]
    )
    assert config.description == ""
    assert config.env == {}
    assert config.timeout == 30
    assert config.retry_attempts == 3


def test_mcp_server_config_timeout_validation():
    """Test timeout field validation."""
    # Valid timeout
    config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"],
        timeout=60
    )
    assert config.timeout == 60
    
    # Invalid timeout (too low)
    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test-package"],
            timeout=0
        )
    
    # Invalid timeout (too high)
    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test-package"],
            timeout=400
        )


def test_session_config_empty_server_name():
    """Test that empty server name raises validation error."""
    with pytest.raises(ValidationError):
        SessionConfig(server_name="")


def test_session_config_server_name_whitespace():
    """Test that server name whitespace is properly stripped."""
    config = SessionConfig(server_name="  test-server  ")
    assert config.server_name == "test-server"


def test_session_config_max_context_length_validation():
    """Test max_context_length field validation."""
    # Valid context length
    config = SessionConfig(
        server_name="test-server",
        max_context_length=50000
    )
    assert config.max_context_length == 50000
    
    # Invalid context length (too low)
    with pytest.raises(ValidationError):
        SessionConfig(
            server_name="test-server",
            max_context_length=500
        )
    
    # Invalid context length (too high)
    with pytest.raises(ValidationError):
        SessionConfig(
            server_name="test-server",
            max_context_length=2000000
        )


def test_connection_status_creation():
    """Test ConnectionStatus model creation."""
    status = ConnectionStatus(
        server_name="test-server",
        connected=True,
        connection_time=datetime.now(),
        available_tools=["tool1", "tool2"]
    )
    assert status.server_name == "test-server"
    assert status.connected is True
    assert status.connection_time is not None
    assert status.error_message is None
    assert status.available_tools == ["tool1", "tool2"]


def test_connection_status_defaults():
    """Test ConnectionStatus default values."""
    status = ConnectionStatus(
        server_name="test-server",
        connected=False
    )
    assert status.connection_time is None
    assert status.error_message is None
    assert status.available_tools == []


def test_connection_status_json_serialization():
    """Test ConnectionStatus JSON serialization with datetime."""
    now = datetime.now()
    status = ConnectionStatus(
        server_name="test-server",
        connected=True,
        connection_time=now
    )
    json_data = status.model_dump(mode='json')
    assert json_data['connection_time'] == now.isoformat()


def test_stream_event_type_enum():
    """Test StreamEventType enum values."""
    assert StreamEventType.TEXT == "text"
    assert StreamEventType.TOOL_USE == "tool_use"
    assert StreamEventType.ERROR == "error"
    assert StreamEventType.COMPLETE == "complete"
    assert StreamEventType.STATUS == "status"


def test_stream_event_creation():
    """Test StreamEvent model creation."""
    event = StreamEvent(
        event_type=StreamEventType.TEXT,
        data="Hello, world!"
    )
    assert event.event_type == StreamEventType.TEXT
    assert event.data == "Hello, world!"
    assert isinstance(event.timestamp, datetime)


def test_stream_event_with_complex_data():
    """Test StreamEvent with complex data structures."""
    tool_data = {
        "tool_name": "test_tool",
        "arguments": {"param1": "value1"},
        "result": {"status": "success"}
    }
    event = StreamEvent(
        event_type=StreamEventType.TOOL_USE,
        data=tool_data
    )
    assert event.event_type == StreamEventType.TOOL_USE
    assert event.data == tool_data


def test_stream_event_json_serialization():
    """Test StreamEvent JSON serialization with datetime."""
    event = StreamEvent(
        event_type=StreamEventType.TEXT,
        data="test data"
    )
    json_data = event.model_dump(mode='json')
    assert json_data['timestamp'] == event.timestamp.isoformat()


def test_tool_info_creation():
    """Test ToolInfo model creation."""
    tool = ToolInfo(
        name="test_tool",
        description="A test tool",
        parameters={"param1": {"type": "string", "description": "Test parameter"}}
    )
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert "param1" in tool.parameters


def test_tool_info_defaults():
    """Test ToolInfo default values."""
    tool = ToolInfo(
        name="test_tool",
        description="A test tool"
    )
    assert tool.parameters == {}


def test_tool_info_empty_name():
    """Test that empty tool name raises validation error."""
    with pytest.raises(ValidationError):
        ToolInfo(
            name="",
            description="A test tool"
        )


def test_tool_info_name_whitespace():
    """Test that tool name whitespace is properly stripped."""
    tool = ToolInfo(
        name="  test_tool  ",
        description="A test tool"
    )
    assert tool.name == "test_tool"


def test_tool_info_whitespace_only_name():
    """Test that whitespace-only tool name raises validation error."""
    with pytest.raises(ValidationError):
        ToolInfo(
            name="   ",
            description="A test tool"
        )


# ConfigManager tests
def test_config_manager_validate_config():
    """Test ConfigManager validate_config method."""
    from eclaircp.config import ConfigManager
    
    manager = ConfigManager()
    config_data = {
        "servers": {
            "test-server": {
                "command": "uvx",
                "args": ["test-package"],
                "description": "Test server"
            }
        }
    }
    
    config = manager.validate_config(config_data)
    assert isinstance(config, ConfigFile)
    assert "test-server" in config.servers
    assert config.servers["test-server"].name == "test-server"


def test_config_manager_validate_config_invalid():
    """Test ConfigManager validate_config with invalid data."""
    from eclaircp.config import ConfigManager, ConfigurationError
    
    manager = ConfigManager()
    config_data = {
        "servers": {
            "test-server": {
                "command": "",  # Invalid empty command
                "args": ["test-package"]
            }
        }
    }
    
    with pytest.raises(ConfigurationError):
        manager.validate_config(config_data)


def test_config_manager_validate_config_empty_servers():
    """Test ConfigManager validate_config with empty servers."""
    from eclaircp.config import ConfigManager, ConfigurationError
    
    manager = ConfigManager()
    config_data = {"servers": {}}
    
    with pytest.raises(ConfigurationError):
        manager.validate_config(config_data)


def test_config_manager_validate_config_with_session():
    """Test ConfigManager validate_config with session configuration."""
    from eclaircp.config import ConfigManager
    
    manager = ConfigManager()
    config_data = {
        "servers": {
            "test-server": {
                "command": "uvx",
                "args": ["test-package"],
                "description": "Test server"
            }
        },
        "default_session": {
            "server_name": "test-server",
            "model": "custom-model",
            "system_prompt": "Custom prompt"
        }
    }
    
    config = manager.validate_config(config_data)
    assert config.default_session is not None
    assert config.default_session.server_name == "test-server"
    assert config.default_session.model == "custom-model"


def test_config_manager_load_config_file_not_found():
    """Test ConfigManager load_config with non-existent file."""
    from eclaircp.config import ConfigManager, ConfigurationError
    
    manager = ConfigManager()
    
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        manager.load_config("/non/existent/file.yaml")


def test_config_manager_save_and_load_config(tmp_path):
    """Test ConfigManager save_config and load_config roundtrip."""
    from eclaircp.config import ConfigManager
    
    manager = ConfigManager()
    
    # Create a test configuration
    server_config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"],
        description="Test server",
        env={"TEST_VAR": "test_value"},
        timeout=60
    )
    session_config = SessionConfig(
        server_name="test-server",
        model="test-model"
    )
    config = ConfigFile(
        servers={"test-server": server_config},
        default_session=session_config
    )
    
    # Save configuration
    config_path = tmp_path / "test_config.yaml"
    manager.save_config(config, str(config_path))
    
    # Load configuration back
    loaded_config = manager.load_config(str(config_path))
    
    # Verify the loaded configuration
    assert "test-server" in loaded_config.servers
    assert loaded_config.servers["test-server"].name == "test-server"
    assert loaded_config.servers["test-server"].command == "uvx"
    assert loaded_config.servers["test-server"].args == ["test-package"]
    assert loaded_config.servers["test-server"].description == "Test server"
    assert loaded_config.servers["test-server"].env == {"TEST_VAR": "test_value"}
    assert loaded_config.servers["test-server"].timeout == 60
    
    assert loaded_config.default_session is not None
    assert loaded_config.default_session.server_name == "test-server"
    assert loaded_config.default_session.model == "test-model"


def test_config_manager_load_config_invalid_yaml(tmp_path):
    """Test ConfigManager load_config with invalid YAML."""
    from eclaircp.config import ConfigManager, ConfigurationError
    
    manager = ConfigManager()
    
    # Create invalid YAML file
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("invalid: yaml: content: [")
    
    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        manager.load_config(str(config_path))


def test_config_manager_load_config_empty_file(tmp_path):
    """Test ConfigManager load_config with empty file."""
    from eclaircp.config import ConfigManager, ConfigurationError
    
    manager = ConfigManager()
    
    # Create empty YAML file
    config_path = tmp_path / "empty.yaml"
    config_path.write_text("")
    
    with pytest.raises(ConfigurationError, match="Configuration file is empty"):
        manager.load_config(str(config_path))


def test_config_manager_save_config_creates_directory(tmp_path):
    """Test ConfigManager save_config creates directory if it doesn't exist."""
    from eclaircp.config import ConfigManager
    
    manager = ConfigManager()
    
    # Create a test configuration
    server_config = MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"]
    )
    config = ConfigFile(servers={"test-server": server_config})
    
    # Save to a path with non-existent directory
    config_path = tmp_path / "subdir" / "config.yaml"
    manager.save_config(config, str(config_path))
    
    # Verify file was created
    assert config_path.exists()
    
    # Verify we can load it back
    loaded_config = manager.load_config(str(config_path))
    assert "test-server" in loaded_config.servers


def test_example_config_file_loads():
    """Test that the example configuration file loads correctly."""
    from eclaircp.config import ConfigManager
    import os
    
    manager = ConfigManager()
    
    # Get the path to the example config file
    example_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "examples",
        "config.yaml"
    )
    
    # Skip test if example file doesn't exist
    if not os.path.exists(example_path):
        pytest.skip("Example config file not found")
    
    # Load the example configuration
    config = manager.load_config(example_path)
    
    # Verify basic structure
    assert isinstance(config, ConfigFile)
    assert len(config.servers) > 0
    
    # Verify specific servers from the example
    if "aws-docs" in config.servers:
        aws_server = config.servers["aws-docs"]
        assert aws_server.command == "uvx"
        assert "awslabs.aws-documentation-mcp-server@latest" in aws_server.args
        assert aws_server.description != ""
    
    # Verify default session if present
    if config.default_session:
        assert config.default_session.server_name in config.servers