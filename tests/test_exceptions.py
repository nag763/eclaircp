"""
Unit tests for EclairCP exception hierarchy and error handling.
"""

import pytest
from eclaircp.exceptions import (
    EclairCPError,
    ConfigurationError,
    ConnectionError,
    SessionError,
    ToolExecutionError,
    ValidationError,
    UserInterruptError,
    ErrorCodes,
    create_configuration_error,
    create_connection_error,
    create_session_error,
)


class TestEclairCPError:
    """Test the base EclairCPError class."""
    
    def test_basic_error_creation(self):
        """Test creating a basic error with just a message."""
        error = EclairCPError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.context == {}
        assert error.suggestions == []
        assert error.error_code is None
        assert error.original_error is None
    
    def test_error_with_context(self):
        """Test creating an error with context information."""
        context = {"file": "test.yaml", "line": 42}
        error = EclairCPError("Test error", context=context)
        
        assert error.context == context
        assert "file" in error.context
        assert error.context["file"] == "test.yaml"
    
    def test_error_with_suggestions(self):
        """Test creating an error with suggestions."""
        suggestions = ["Check the file", "Try again"]
        error = EclairCPError("Test error", suggestions=suggestions)
        
        assert error.suggestions == suggestions
        assert len(error.suggestions) == 2
    
    def test_error_with_all_parameters(self):
        """Test creating an error with all parameters."""
        original = ValueError("Original error")
        error = EclairCPError(
            "Test error",
            context={"key": "value"},
            suggestions=["Fix it"],
            error_code="TEST_001",
            original_error=original
        )
        
        assert error.message == "Test error"
        assert error.context == {"key": "value"}
        assert error.suggestions == ["Fix it"]
        assert error.error_code == "TEST_001"
        assert error.original_error is original
    
    def test_add_context(self):
        """Test adding context to an error."""
        error = EclairCPError("Test error")
        error.add_context("key1", "value1")
        error.add_context("key2", 42)
        
        assert error.context["key1"] == "value1"
        assert error.context["key2"] == 42
        assert len(error.context) == 2
    
    def test_add_suggestion(self):
        """Test adding suggestions to an error."""
        error = EclairCPError("Test error")
        error.add_suggestion("First suggestion")
        error.add_suggestion("Second suggestion")
        
        assert len(error.suggestions) == 2
        assert "First suggestion" in error.suggestions
        assert "Second suggestion" in error.suggestions
    
    def test_formatted_message_basic(self):
        """Test formatted message with just the basic message."""
        error = EclairCPError("Test error")
        formatted = error.get_formatted_message()
        assert formatted == "Test error"
    
    def test_formatted_message_with_context(self):
        """Test formatted message with context."""
        error = EclairCPError("Test error", context={"file": "test.yaml"})
        formatted = error.get_formatted_message()
        
        assert "Test error" in formatted
        assert "Context:" in formatted
        assert "file: test.yaml" in formatted
    
    def test_formatted_message_with_suggestions(self):
        """Test formatted message with suggestions."""
        error = EclairCPError("Test error", suggestions=["Fix it", "Try again"])
        formatted = error.get_formatted_message()
        
        assert "Test error" in formatted
        assert "Suggestions:" in formatted
        assert "• Fix it" in formatted
        assert "• Try again" in formatted
    
    def test_formatted_message_complete(self):
        """Test formatted message with context and suggestions."""
        error = EclairCPError(
            "Test error",
            context={"file": "test.yaml", "line": 10},
            suggestions=["Check syntax", "Validate format"]
        )
        formatted = error.get_formatted_message()
        
        assert "Test error" in formatted
        assert "Context:" in formatted
        assert "file: test.yaml" in formatted
        assert "line: 10" in formatted
        assert "Suggestions:" in formatted
        assert "• Check syntax" in formatted
        assert "• Validate format" in formatted


class TestConfigurationError:
    """Test the ConfigurationError class."""
    
    def test_basic_configuration_error(self):
        """Test creating a basic configuration error."""
        error = ConfigurationError("Config error")
        assert isinstance(error, EclairCPError)
        assert str(error) == "Config error"
        assert len(error.suggestions) > 0  # Should have default suggestions
    
    def test_configuration_error_with_path(self):
        """Test configuration error with config path."""
        error = ConfigurationError("Config error", config_path="/path/to/config.yaml")
        assert error.context["config_path"] == "/path/to/config.yaml"
    
    def test_configuration_error_with_field(self):
        """Test configuration error with field name."""
        error = ConfigurationError("Config error", field_name="servers")
        assert error.context["field_name"] == "servers"
    
    def test_configuration_error_default_suggestions(self):
        """Test that configuration errors have default suggestions."""
        error = ConfigurationError("Config error")
        assert len(error.suggestions) > 0
        assert any("configuration file" in s.lower() for s in error.suggestions)
        assert any("yaml" in s.lower() for s in error.suggestions)


class TestConnectionError:
    """Test the ConnectionError class."""
    
    def test_basic_connection_error(self):
        """Test creating a basic connection error."""
        error = ConnectionError("Connection failed")
        assert isinstance(error, EclairCPError)
        assert str(error) == "Connection failed"
        assert len(error.suggestions) > 0  # Should have default suggestions
    
    def test_connection_error_with_server(self):
        """Test connection error with server information."""
        error = ConnectionError(
            "Connection failed",
            server_name="test-server",
            server_command="uvx test-server",
            timeout=30
        )
        assert error.context["server_name"] == "test-server"
        assert error.context["server_command"] == "uvx test-server"
        assert error.context["timeout"] == 30
    
    def test_connection_error_default_suggestions(self):
        """Test that connection errors have default suggestions."""
        error = ConnectionError("Connection failed")
        assert len(error.suggestions) > 0
        assert any("server command" in s.lower() for s in error.suggestions)
        assert any("dependencies" in s.lower() for s in error.suggestions)


class TestSessionError:
    """Test the SessionError class."""
    
    def test_basic_session_error(self):
        """Test creating a basic session error."""
        error = SessionError("Session failed")
        assert isinstance(error, EclairCPError)
        assert str(error) == "Session failed"
        assert len(error.suggestions) > 0  # Should have default suggestions
    
    def test_session_error_with_details(self):
        """Test session error with session details."""
        error = SessionError(
            "Session failed",
            session_id="sess_123",
            agent_model="claude-3-sonnet",
            tool_name="test_tool"
        )
        assert error.context["session_id"] == "sess_123"
        assert error.context["agent_model"] == "claude-3-sonnet"
        assert error.context["tool_name"] == "test_tool"
    
    def test_session_error_default_suggestions(self):
        """Test that session errors have default suggestions."""
        error = SessionError("Session failed")
        assert len(error.suggestions) > 0
        assert any("session" in s.lower() for s in error.suggestions)
        assert any("mcp server" in s.lower() for s in error.suggestions)


class TestToolExecutionError:
    """Test the ToolExecutionError class."""
    
    def test_basic_tool_error(self):
        """Test creating a basic tool execution error."""
        error = ToolExecutionError("Tool failed")
        assert isinstance(error, EclairCPError)
        assert str(error) == "Tool failed"
        assert len(error.suggestions) > 0  # Should have default suggestions
    
    def test_tool_error_with_details(self):
        """Test tool execution error with tool details."""
        error = ToolExecutionError(
            "Tool failed",
            tool_name="test_tool",
            tool_args={"param": "value"},
            server_name="test-server"
        )
        assert error.context["tool_name"] == "test_tool"
        assert error.context["tool_args"] == {"param": "value"}
        assert error.context["server_name"] == "test-server"
    
    def test_tool_error_default_suggestions(self):
        """Test that tool execution errors have default suggestions."""
        error = ToolExecutionError("Tool failed")
        assert len(error.suggestions) > 0
        assert any("arguments" in s.lower() for s in error.suggestions)
        assert any("tool" in s.lower() for s in error.suggestions)


class TestValidationError:
    """Test the ValidationError class."""
    
    def test_basic_validation_error(self):
        """Test creating a basic validation error."""
        error = ValidationError("Validation failed")
        assert isinstance(error, EclairCPError)
        assert str(error) == "Validation failed"
        assert len(error.suggestions) > 0  # Should have default suggestions
    
    def test_validation_error_with_field(self):
        """Test validation error with field details."""
        error = ValidationError(
            "Validation failed",
            field_name="timeout",
            field_value=-1,
            expected_type="positive integer"
        )
        assert error.context["field_name"] == "timeout"
        assert error.context["field_value"] == -1
        assert error.context["expected_type"] == "positive integer"
    
    def test_validation_error_default_suggestions(self):
        """Test that validation errors have default suggestions."""
        error = ValidationError("Validation failed")
        assert len(error.suggestions) > 0
        assert any("format" in s.lower() for s in error.suggestions)
        assert any("schema" in s.lower() for s in error.suggestions)


class TestUserInterruptError:
    """Test the UserInterruptError class."""
    
    def test_basic_user_interrupt(self):
        """Test creating a basic user interrupt error."""
        error = UserInterruptError()
        assert isinstance(error, EclairCPError)
        assert "cancelled by user" in str(error).lower()
        assert len(error.suggestions) == 0  # No suggestions for user interrupts
    
    def test_user_interrupt_with_operation(self):
        """Test user interrupt error with operation context."""
        error = UserInterruptError("Custom message", operation="server_selection")
        assert str(error) == "Custom message"
        assert error.context["operation"] == "server_selection"
        assert len(error.suggestions) == 0


class TestErrorCodes:
    """Test the ErrorCodes constants."""
    
    def test_error_codes_exist(self):
        """Test that all expected error codes are defined."""
        # Configuration error codes
        assert hasattr(ErrorCodes, 'CONFIG_FILE_NOT_FOUND')
        assert hasattr(ErrorCodes, 'CONFIG_INVALID_YAML')
        assert hasattr(ErrorCodes, 'CONFIG_VALIDATION_FAILED')
        assert hasattr(ErrorCodes, 'CONFIG_MISSING_SERVERS')
        
        # Connection error codes
        assert hasattr(ErrorCodes, 'CONNECTION_FAILED')
        assert hasattr(ErrorCodes, 'CONNECTION_TIMEOUT')
        assert hasattr(ErrorCodes, 'CONNECTION_LOST')
        assert hasattr(ErrorCodes, 'SERVER_NOT_FOUND')
        
        # Session error codes
        assert hasattr(ErrorCodes, 'SESSION_INIT_FAILED')
        assert hasattr(ErrorCodes, 'SESSION_AGENT_ERROR')
        assert hasattr(ErrorCodes, 'SESSION_CONTEXT_ERROR')
        
        # Tool error codes
        assert hasattr(ErrorCodes, 'TOOL_NOT_FOUND')
        assert hasattr(ErrorCodes, 'TOOL_EXECUTION_FAILED')
        assert hasattr(ErrorCodes, 'TOOL_INVALID_ARGS')
        
        # Validation error codes
        assert hasattr(ErrorCodes, 'VALIDATION_FAILED')
        assert hasattr(ErrorCodes, 'INVALID_INPUT')
        
        # User interaction error codes
        assert hasattr(ErrorCodes, 'USER_CANCELLED')
    
    def test_error_codes_are_strings(self):
        """Test that error codes are string constants."""
        assert isinstance(ErrorCodes.CONFIG_FILE_NOT_FOUND, str)
        assert isinstance(ErrorCodes.CONNECTION_FAILED, str)
        assert isinstance(ErrorCodes.SESSION_INIT_FAILED, str)


class TestErrorFactoryFunctions:
    """Test the error factory functions."""
    
    def test_create_configuration_error_basic(self):
        """Test creating a configuration error with factory function."""
        error = create_configuration_error("Config error")
        assert isinstance(error, ConfigurationError)
        assert str(error) == "Config error"
        assert error.error_code == ErrorCodes.CONFIG_VALIDATION_FAILED
    
    def test_create_configuration_error_not_found(self):
        """Test creating a 'not found' configuration error."""
        error = create_configuration_error("File not found", config_path="/path/to/config")
        assert error.error_code == ErrorCodes.CONFIG_FILE_NOT_FOUND
        assert error.context["config_path"] == "/path/to/config"
    
    def test_create_configuration_error_yaml(self):
        """Test creating a YAML configuration error."""
        error = create_configuration_error("Invalid YAML syntax")
        assert error.error_code == ErrorCodes.CONFIG_INVALID_YAML
    
    def test_create_connection_error_basic(self):
        """Test creating a connection error with factory function."""
        error = create_connection_error("Connection failed")
        assert isinstance(error, ConnectionError)
        assert str(error) == "Connection failed"
        assert error.error_code == ErrorCodes.CONNECTION_FAILED
    
    def test_create_connection_error_timeout(self):
        """Test creating a timeout connection error."""
        error = create_connection_error("Connection timeout", timeout=30)
        assert error.error_code == ErrorCodes.CONNECTION_TIMEOUT
        assert error.context["timeout"] == 30
    
    def test_create_connection_error_lost(self):
        """Test creating a connection lost error."""
        error = create_connection_error("Connection lost", server_name="test-server")
        assert error.error_code == ErrorCodes.CONNECTION_LOST
        assert error.context["server_name"] == "test-server"
    
    def test_create_session_error_basic(self):
        """Test creating a session error with factory function."""
        error = create_session_error("Session failed")
        assert isinstance(error, SessionError)
        assert str(error) == "Session failed"
        assert error.error_code == ErrorCodes.SESSION_INIT_FAILED
    
    def test_create_session_error_agent(self):
        """Test creating an agent session error."""
        error = create_session_error("Agent error", agent_model="claude-3-sonnet")
        assert error.error_code == ErrorCodes.SESSION_AGENT_ERROR
        assert error.context["agent_model"] == "claude-3-sonnet"
    
    def test_create_session_error_context(self):
        """Test creating a context session error."""
        error = create_session_error("Context error", session_id="sess_123")
        assert error.error_code == ErrorCodes.SESSION_CONTEXT_ERROR
        assert error.context["session_id"] == "sess_123"
    
    def test_factory_functions_with_original_error(self):
        """Test factory functions with original error chaining."""
        original = ValueError("Original error")
        
        config_error = create_configuration_error("Config error", original_error=original)
        assert config_error.original_error is original
        
        conn_error = create_connection_error("Connection error", original_error=original)
        assert conn_error.original_error is original
        
        session_error = create_session_error("Session error", original_error=original)
        assert session_error.original_error is original


class TestErrorIntegration:
    """Test error integration scenarios."""
    
    def test_error_chaining(self):
        """Test that errors can be properly chained."""
        original = ValueError("Original validation error")
        config_error = create_configuration_error(
            "Configuration validation failed",
            original_error=original
        )
        
        # Test that the chain is preserved
        assert config_error.original_error is original
        assert config_error.__cause__ is original
    
    def test_error_context_accumulation(self):
        """Test that error context can be accumulated."""
        error = ConfigurationError("Base error")
        error.add_context("file", "config.yaml")
        error.add_context("section", "servers")
        error.add_suggestion("Check the file format")
        error.add_suggestion("Validate the syntax")
        
        formatted = error.get_formatted_message()
        assert "file: config.yaml" in formatted
        assert "section: servers" in formatted
        assert "• Check the file format" in formatted
        assert "• Validate the syntax" in formatted
    
    def test_error_inheritance_chain(self):
        """Test that all custom errors inherit from EclairCPError."""
        errors = [
            ConfigurationError("test"),
            ConnectionError("test"),
            SessionError("test"),
            ToolExecutionError("test"),
            ValidationError("test"),
            UserInterruptError("test"),
        ]
        
        for error in errors:
            assert isinstance(error, EclairCPError)
            assert isinstance(error, Exception)