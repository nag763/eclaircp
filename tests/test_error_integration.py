"""
Integration tests for EclairCP error handling, display, and recovery.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

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
from eclaircp.error_logging import (
    EclairCPLogger,
    get_logger,
    setup_logging,
    log_error,
    log_debug,
    log_info,
    log_warning,
)
from eclaircp.ui import StreamingDisplay
from rich.console import Console


class TestErrorLogging:
    """Test error logging functionality."""
    
    def test_logger_initialization(self):
        """Test logger initialization with different configurations."""
        # Test with default configuration
        logger = EclairCPLogger()
        assert logger.logger.name == "eclaircp"
        assert logger.logger.level == 20  # INFO level
    
    def test_logger_with_file(self):
        """Test logger with file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
        
        try:
            logger = EclairCPLogger(log_file=log_file, log_level="DEBUG")
            logger.log_info("Test message")
            
            # Check that log file was created and contains the message
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
                assert "eclaircp" in content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_log_eclaircp_error(self):
        """Test logging EclairCP errors with context."""
        logger = EclairCPLogger()
        
        error = ConfigurationError(
            "Test config error",
            config_path="/test/config.yaml",
            error_code=ErrorCodes.CONFIG_VALIDATION_FAILED
        )
        error.add_context("section", "servers")
        error.add_suggestion("Check the configuration")
        
        # Mock the logger to capture the call
        with patch.object(logger.logger, 'error') as mock_error:
            logger.log_error(error)
            
            # Verify the error was logged with proper information
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Test config error" in call_args[0][1]
            
            # Check that extra information was included
            extra = call_args[1]['extra']
            assert 'error_details' in extra
            error_details = extra['error_details']
            assert error_details['error_type'] == 'ConfigurationError'
            assert error_details['error_code'] == ErrorCodes.CONFIG_VALIDATION_FAILED
            assert 'section' in error_details['error_context']
    
    def test_log_configuration_error(self):
        """Test configuration-specific error logging."""
        logger = EclairCPLogger()
        
        error = ValueError("Invalid YAML")
        
        with patch.object(logger, 'log_error') as mock_log:
            logger.log_configuration_error(
                error, 
                config_path="/test/config.yaml",
                config_section="servers"
            )
            
            mock_log.assert_called_once_with(
                error,
                context={
                    "config_path": "/test/config.yaml",
                    "config_section": "servers"
                }
            )
    
    def test_log_connection_error(self):
        """Test connection-specific error logging."""
        logger = EclairCPLogger()
        
        error = ConnectionError("Connection failed")
        
        with patch.object(logger, 'log_error') as mock_log:
            logger.log_connection_error(
                error,
                server_name="test-server",
                server_command="uvx test-server",
                connection_attempt=2
            )
            
            mock_log.assert_called_once_with(
                error,
                context={
                    "server_name": "test-server",
                    "server_command": "uvx test-server",
                    "connection_attempt": 2
                }
            )
    
    def test_global_logger_functions(self):
        """Test global logger convenience functions."""
        with patch('eclaircp.error_logging._global_logger') as mock_logger:
            mock_instance = Mock()
            mock_logger = mock_instance
            
            # Test that functions call the global logger
            with patch('eclaircp.error_logging.get_logger', return_value=mock_instance):
                error = ValueError("Test error")
                log_error(error, context={"test": "value"})
                log_debug("Debug message")
                log_info("Info message")
                log_warning("Warning message")
                
                mock_instance.log_error.assert_called_once_with(error, context={"test": "value"})
                mock_instance.log_debug.assert_called_once_with("Debug message")
                mock_instance.log_info.assert_called_once_with("Info message")
                mock_instance.log_warning.assert_called_once_with("Warning message")


class TestErrorDisplay:
    """Test error display functionality in UI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a console that captures output
        self.output = StringIO()
        self.console = Console(file=self.output, width=80)
        self.display = StreamingDisplay(console=self.console)
    
    def test_show_eclaircp_error_basic(self):
        """Test displaying a basic EclairCP error."""
        error = ConfigurationError("Test configuration error")
        
        self.display.show_eclaircp_error(error)
        output = self.output.getvalue()
        
        assert "Configuration Error" in output
        assert "Test configuration error" in output
        assert "⚙️" in output  # Configuration error icon
    
    def test_show_eclaircp_error_with_context(self):
        """Test displaying error with context information."""
        error = ConnectionError(
            "Connection failed",
            server_name="test-server",
            timeout=30
        )
        error.add_context("retry_count", 3)
        
        self.display.show_eclaircp_error(error)
        output = self.output.getvalue()
        
        assert "Connection Error" in output
        assert "Connection failed" in output
        assert "Context" in output
        assert "Server Name: test-server" in output
        assert "Timeout: 30" in output
        assert "Retry Count: 3" in output
    
    def test_show_eclaircp_error_with_suggestions(self):
        """Test displaying error with suggestions."""
        error = ValidationError("Invalid input")
        error.add_suggestion("Check the input format")
        error.add_suggestion("Refer to the documentation")
        
        self.display.show_eclaircp_error(error)
        output = self.output.getvalue()
        
        assert "Validation Error" in output
        assert "Invalid input" in output
        assert "Suggestions" in output
        assert "• Check the input format" in output
        assert "• Refer to the documentation" in output
    
    def test_show_eclaircp_error_with_original_error(self):
        """Test displaying error with original error chain."""
        original = ValueError("Original validation error")
        error = create_configuration_error(
            "Configuration validation failed",
            original_error=original
        )
        
        self.display.show_eclaircp_error(error)
        output = self.output.getvalue()
        
        assert "Configuration Error" in output
        assert "Configuration validation failed" in output
        assert "Original Error" in output
        assert "ValueError: Original validation error" in output
    
    def test_show_error_with_recovery_no_options(self):
        """Test error display with recovery when no options provided."""
        error = SessionError("Session failed")
        
        with patch('rich.prompt.Prompt.ask', return_value='5'):  # Choose exit
            result = self.display.show_error_with_recovery(error)
            
        assert result is None
        output = self.output.getvalue()
        assert "Session Error" in output
        assert "Recovery Options" in output
        assert "Restart session" in output  # Default recovery option
        assert "Exit" in output
    
    def test_show_error_with_recovery_custom_options(self):
        """Test error display with custom recovery options."""
        error = ToolExecutionError("Tool failed")
        recovery_options = ["Retry with different args", "Skip this tool"]
        
        with patch('rich.prompt.Prompt.ask', return_value='1'):
            result = self.display.show_error_with_recovery(error, recovery_options)
            
        assert result == "Retry with different args"
        output = self.output.getvalue()
        assert "Tool Execution Error" in output
        assert "Recovery Options" in output
        assert "Retry with different args" in output
        assert "Skip this tool" in output
    
    def test_show_error_with_recovery_user_cancellation(self):
        """Test error recovery when user cancels."""
        error = ConnectionError("Connection failed")
        
        with patch('rich.prompt.Prompt.ask', side_effect=KeyboardInterrupt):
            result = self.display.show_error_with_recovery(error)
            
        assert result is None
        output = self.output.getvalue()
        assert "Operation cancelled" in output
    
    def test_error_display_info_for_different_types(self):
        """Test that different error types get appropriate display info."""
        test_cases = [
            (ConfigurationError("test"), "⚙️", "Configuration Error"),
            (ConnectionError("test"), "🔌", "Connection Error"),
            (SessionError("test"), "💬", "Session Error"),
            (ToolExecutionError("test"), "🛠️", "Tool Execution Error"),
            (ValidationError("test"), "✅", "Validation Error"),
            (UserInterruptError("test"), "⏹️", "Operation Cancelled"),
            (EclairCPError("test"), "❌", "Error"),  # Base error
        ]
        
        for error, expected_icon, expected_title in test_cases:
            info = self.display._get_error_display_info(error)
            assert info["icon"] == expected_icon
            assert info["title"] == expected_title
    
    def test_default_recovery_options(self):
        """Test default recovery options for different error types."""
        test_cases = [
            (ConfigurationError("test"), "Edit configuration file"),
            (ConnectionError("test"), "Retry connection"),
            (SessionError("test"), "Restart session"),
            (ToolExecutionError("test"), "Retry tool execution"),
            (ValidationError("test"), "Correct the input"),
            (EclairCPError("test"), "Retry operation"),  # Base error
        ]
        
        for error, expected_option in test_cases:
            options = self.display._get_default_recovery_options(error)
            assert len(options) > 0
            assert expected_option in options


class TestErrorIntegrationScenarios:
    """Test complete error handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output = StringIO()
        self.console = Console(file=self.output, width=80)
        self.display = StreamingDisplay(console=self.console)
        self.logger = EclairCPLogger()
    
    def test_configuration_error_scenario(self):
        """Test complete configuration error handling scenario."""
        # Simulate a configuration file error
        config_path = "/test/config.yaml"
        original_error = FileNotFoundError("No such file or directory")
        
        error = create_configuration_error(
            f"Configuration file not found: {config_path}",
            config_path=config_path,
            original_error=original_error
        )
        
        # Log the error
        with patch.object(self.logger.logger, 'error') as mock_log:
            self.logger.log_configuration_error(error, config_path=config_path)
            mock_log.assert_called_once()
        
        # Display the error with recovery
        with patch('rich.prompt.Prompt.ask', return_value='1'):  # Choose first option
            recovery_choice = self.display.show_error_with_recovery(error)
        
        assert recovery_choice == "Edit configuration file"
        output = self.output.getvalue()
        assert "Configuration Error" in output
        assert config_path in output
        assert "Original Error" in output
        assert "FileNotFoundError" in output
    
    def test_connection_error_scenario(self):
        """Test complete connection error handling scenario."""
        # Simulate a connection timeout error
        server_name = "test-server"
        server_command = "uvx test-server"
        timeout = 30
        
        error = create_connection_error(
            f"Connection to {server_name} timed out after {timeout} seconds",
            server_name=server_name,
            server_command=server_command,
            timeout=timeout
        )
        
        # Log the error
        with patch.object(self.logger.logger, 'error') as mock_log:
            self.logger.log_connection_error(
                error,
                server_name=server_name,
                server_command=server_command,
                connection_attempt=2
            )
            mock_log.assert_called_once()
        
        # Display the error with recovery
        with patch('rich.prompt.Prompt.ask', return_value='2'):  # Choose second option
            recovery_choice = self.display.show_error_with_recovery(error)
        
        assert recovery_choice == "Select different server"
        output = self.output.getvalue()
        assert "Connection Error" in output
        assert server_name in output
        assert str(timeout) in output
    
    def test_session_error_scenario(self):
        """Test complete session error handling scenario."""
        # Simulate a session initialization error
        session_id = "sess_123"
        agent_model = "claude-3-sonnet"
        
        error = create_session_error(
            "Failed to initialize agent with specified model",
            session_id=session_id,
            agent_model=agent_model
        )
        
        # Log the error
        with patch.object(self.logger.logger, 'error') as mock_log:
            self.logger.log_session_error(
                error,
                session_id=session_id,
                agent_model=agent_model,
                message_count=0
            )
            mock_log.assert_called_once()
        
        # Display the error with recovery
        with patch('rich.prompt.Prompt.ask', return_value='2'):  # Choose second option
            recovery_choice = self.display.show_error_with_recovery(error)
        
        assert recovery_choice == "Change agent model"
        output = self.output.getvalue()
        assert "Session Error" in output
        assert session_id in output
        assert agent_model in output
    
    def test_error_chaining_and_context_preservation(self):
        """Test that error context and chaining is preserved through the system."""
        # Create a chain of errors
        original = ValueError("Invalid YAML syntax at line 15")
        config_error = create_configuration_error(
            "Failed to parse configuration file",
            config_path="/test/config.yaml",
            field_name="servers",
            original_error=original
        )
        
        # Add additional context
        config_error.add_context("line_number", 15)
        config_error.add_context("yaml_section", "servers.aws-docs")
        
        # Verify error chaining
        assert config_error.original_error is original
        assert config_error.__cause__ is original
        
        # Verify context preservation
        assert config_error.context["config_path"] == "/test/config.yaml"
        assert config_error.context["field_name"] == "servers"
        assert config_error.context["line_number"] == 15
        assert config_error.context["yaml_section"] == "servers.aws-docs"
        
        # Test that display shows all information
        self.display.show_eclaircp_error(config_error)
        output = self.output.getvalue()
        
        assert "Configuration Error" in output
        assert "Failed to parse configuration file" in output
        assert "Context" in output
        assert "/test/config.yaml" in output
        assert "servers" in output
        assert "15" in output
        assert "Original Error" in output
        assert "ValueError: Invalid YAML syntax at line 15" in output
    
    def test_logging_integration_with_file_output(self):
        """Test that logging works correctly with file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            # Set up logger with file output
            logger = setup_logging(log_file=log_file, log_level="DEBUG")
            
            # Create and log various types of errors
            config_error = ConfigurationError("Config test error")
            connection_error = ConnectionError("Connection test error")
            session_error = SessionError("Session test error")
            
            logger.log_error(config_error)
            logger.log_error(connection_error)
            logger.log_error(session_error)
            logger.log_info("Test info message")
            logger.log_debug("Test debug message")
            
            # Verify log file contents
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            assert "Config test error" in log_content
            assert "Connection test error" in log_content
            assert "Session test error" in log_content
            assert "Test info message" in log_content
            assert "Test debug message" in log_content
            assert "eclaircp" in log_content
            
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)