"""
EclairCP exception hierarchy and error handling utilities.

This module defines the complete exception hierarchy for EclairCP, providing
structured error handling with context and user-friendly suggestions.
"""

from typing import Optional, List, Dict, Any


class EclairCPError(Exception):
    """
    Base exception for all EclairCP errors.
    
    Provides common functionality for error context, suggestions, and formatting.
    """
    
    def __init__(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize EclairCP error with context and suggestions.
        
        Args:
            message: Human-readable error message
            context: Additional context information for debugging
            suggestions: List of actionable suggestions for the user
            error_code: Unique error code for programmatic handling
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
        self.error_code = error_code
        self.original_error = original_error
    
    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the error."""
        self.context[key] = value
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to help resolve the error."""
        self.suggestions.append(suggestion)
    
    def get_formatted_message(self) -> str:
        """Get a formatted error message with context and suggestions."""
        parts = [self.message]
        
        if self.context:
            parts.append("\nContext:")
            for key, value in self.context.items():
                parts.append(f"  {key}: {value}")
        
        if self.suggestions:
            parts.append("\nSuggestions:")
            for suggestion in self.suggestions:
                parts.append(f"  • {suggestion}")
        
        return "\n".join(parts)


class ConfigurationError(EclairCPError):
    """
    Configuration-related errors.
    
    Raised when there are issues with configuration files, validation,
    or server specifications.
    """
    
    def __init__(
        self,
        message: str,
        *,
        config_path: Optional[str] = None,
        field_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_path: Path to the configuration file with issues
            field_name: Specific configuration field that caused the error
            **kwargs: Additional arguments passed to EclairCPError
        """
        super().__init__(message, **kwargs)
        
        if config_path:
            self.add_context("config_path", config_path)
        if field_name:
            self.add_context("field_name", field_name)
        
        # Add common configuration suggestions
        if not self.suggestions:
            self._add_default_config_suggestions()
    
    def _add_default_config_suggestions(self) -> None:
        """Add default suggestions for configuration errors."""
        self.add_suggestion("Check the configuration file syntax and structure")
        self.add_suggestion("Refer to examples/config.yaml for proper format")
        self.add_suggestion("Validate YAML syntax using an online validator")


class ConnectionError(EclairCPError):
    """
    MCP server connection-related errors.
    
    Raised when there are issues connecting to, communicating with,
    or maintaining connections to MCP servers.
    """
    
    def __init__(
        self,
        message: str,
        *,
        server_name: Optional[str] = None,
        server_command: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize connection error.
        
        Args:
            message: Error message
            server_name: Name of the MCP server that failed
            server_command: Command used to start the server
            timeout: Connection timeout value
            **kwargs: Additional arguments passed to EclairCPError
        """
        super().__init__(message, **kwargs)
        
        if server_name:
            self.add_context("server_name", server_name)
        if server_command:
            self.add_context("server_command", server_command)
        if timeout:
            self.add_context("timeout", timeout)
        
        # Add common connection suggestions
        if not self.suggestions:
            self._add_default_connection_suggestions()
    
    def _add_default_connection_suggestions(self) -> None:
        """Add default suggestions for connection errors."""
        self.add_suggestion("Verify the server command and arguments are correct")
        self.add_suggestion("Check if required dependencies are installed (e.g., uvx, uv)")
        self.add_suggestion("Ensure environment variables are properly set")
        self.add_suggestion("Try increasing the connection timeout value")
        self.add_suggestion("Check network connectivity if using remote servers")


class SessionError(EclairCPError):
    """
    Session management and conversation-related errors.
    
    Raised when there are issues with session initialization, management,
    or conversation processing through Strands agents.
    """
    
    def __init__(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
        agent_model: Optional[str] = None,
        tool_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize session error.
        
        Args:
            message: Error message
            session_id: ID of the session that encountered the error
            agent_model: Model being used by the Strands agent
            tool_name: Name of the tool that caused the error
            **kwargs: Additional arguments passed to EclairCPError
        """
        super().__init__(message, **kwargs)
        
        if session_id:
            self.add_context("session_id", session_id)
        if agent_model:
            self.add_context("agent_model", agent_model)
        if tool_name:
            self.add_context("tool_name", tool_name)
        
        # Add common session suggestions
        if not self.suggestions:
            self._add_default_session_suggestions()
    
    def _add_default_session_suggestions(self) -> None:
        """Add default suggestions for session errors."""
        self.add_suggestion("Try restarting the session")
        self.add_suggestion("Check if the MCP server is still connected")
        self.add_suggestion("Verify the agent model is available and accessible")
        self.add_suggestion("Reduce the complexity of your request")


class ToolExecutionError(EclairCPError):
    """
    MCP tool execution errors.
    
    Raised when there are issues executing MCP tools or processing
    their results.
    """
    
    def __init__(
        self,
        message: str,
        *,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        server_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tool execution error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that failed
            tool_args: Arguments passed to the tool
            server_name: Name of the MCP server hosting the tool
            **kwargs: Additional arguments passed to EclairCPError
        """
        super().__init__(message, **kwargs)
        
        if tool_name:
            self.add_context("tool_name", tool_name)
        if tool_args:
            self.add_context("tool_args", tool_args)
        if server_name:
            self.add_context("server_name", server_name)
        
        # Add common tool execution suggestions
        if not self.suggestions:
            self._add_default_tool_suggestions()
    
    def _add_default_tool_suggestions(self) -> None:
        """Add default suggestions for tool execution errors."""
        self.add_suggestion("Check if the tool arguments are valid and complete")
        self.add_suggestion("Verify the MCP server supports this tool")
        self.add_suggestion("Try using the tool with simpler arguments")
        self.add_suggestion("Check the MCP server logs for more details")


class ValidationError(EclairCPError):
    """
    Data validation errors.
    
    Raised when input data fails validation checks or doesn't meet
    expected formats or constraints.
    """
    
    def __init__(
        self,
        message: str,
        *,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            expected_type: Expected type or format
            **kwargs: Additional arguments passed to EclairCPError
        """
        super().__init__(message, **kwargs)
        
        if field_name:
            self.add_context("field_name", field_name)
        if field_value is not None:
            self.add_context("field_value", field_value)
        if expected_type:
            self.add_context("expected_type", expected_type)
        
        # Add common validation suggestions
        if not self.suggestions:
            self._add_default_validation_suggestions()
    
    def _add_default_validation_suggestions(self) -> None:
        """Add default suggestions for validation errors."""
        self.add_suggestion("Check the data format and type requirements")
        self.add_suggestion("Refer to the documentation for expected values")
        self.add_suggestion("Validate your input against the schema")


class UserInterruptError(EclairCPError):
    """
    User interruption errors.
    
    Raised when the user cancels an operation or interrupts execution.
    """
    
    def __init__(
        self,
        message: str = "Operation cancelled by user",
        *,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize user interrupt error.
        
        Args:
            message: Error message
            operation: Name of the operation that was interrupted
            **kwargs: Additional arguments passed to EclairCPError
        """
        super().__init__(message, **kwargs)
        
        if operation:
            self.add_context("operation", operation)
        
        # User interrupts typically don't need suggestions
        self.suggestions = []


# Error code constants for programmatic handling
class ErrorCodes:
    """Constants for error codes used throughout EclairCP."""
    
    # Configuration errors
    CONFIG_FILE_NOT_FOUND = "CONFIG_001"
    CONFIG_INVALID_YAML = "CONFIG_002"
    CONFIG_VALIDATION_FAILED = "CONFIG_003"
    CONFIG_MISSING_SERVERS = "CONFIG_004"
    
    # Connection errors
    CONNECTION_FAILED = "CONN_001"
    CONNECTION_TIMEOUT = "CONN_002"
    CONNECTION_LOST = "CONN_003"
    SERVER_NOT_FOUND = "CONN_004"
    
    # Session errors
    SESSION_INIT_FAILED = "SESS_001"
    SESSION_AGENT_ERROR = "SESS_002"
    SESSION_CONTEXT_ERROR = "SESS_003"
    
    # Tool execution errors
    TOOL_NOT_FOUND = "TOOL_001"
    TOOL_EXECUTION_FAILED = "TOOL_002"
    TOOL_INVALID_ARGS = "TOOL_003"
    
    # Validation errors
    VALIDATION_FAILED = "VALID_001"
    INVALID_INPUT = "VALID_002"
    
    # User interaction errors
    USER_CANCELLED = "USER_001"


def create_configuration_error(
    message: str,
    config_path: Optional[str] = None,
    field_name: Optional[str] = None,
    original_error: Optional[Exception] = None
) -> ConfigurationError:
    """
    Factory function to create configuration errors with appropriate context.
    
    Args:
        message: Error message
        config_path: Path to configuration file
        field_name: Field that caused the error
        original_error: Original exception
        
    Returns:
        ConfigurationError: Configured error instance
    """
    error_code = ErrorCodes.CONFIG_VALIDATION_FAILED
    if "not found" in message.lower():
        error_code = ErrorCodes.CONFIG_FILE_NOT_FOUND
    elif "yaml" in message.lower():
        error_code = ErrorCodes.CONFIG_INVALID_YAML
    
    error = ConfigurationError(
        message,
        config_path=config_path,
        field_name=field_name,
        error_code=error_code,
        original_error=original_error
    )
    
    # Set the __cause__ attribute for proper exception chaining
    if original_error:
        error.__cause__ = original_error
    
    return error


def create_connection_error(
    message: str,
    server_name: Optional[str] = None,
    server_command: Optional[str] = None,
    timeout: Optional[int] = None,
    original_error: Optional[Exception] = None
) -> ConnectionError:
    """
    Factory function to create connection errors with appropriate context.
    
    Args:
        message: Error message
        server_name: Name of the server
        server_command: Server command
        timeout: Connection timeout
        original_error: Original exception
        
    Returns:
        ConnectionError: Configured error instance
    """
    error_code = ErrorCodes.CONNECTION_FAILED
    if "timeout" in message.lower():
        error_code = ErrorCodes.CONNECTION_TIMEOUT
    elif "lost" in message.lower():
        error_code = ErrorCodes.CONNECTION_LOST
    
    error = ConnectionError(
        message,
        server_name=server_name,
        server_command=server_command,
        timeout=timeout,
        error_code=error_code,
        original_error=original_error
    )
    
    # Set the __cause__ attribute for proper exception chaining
    if original_error:
        error.__cause__ = original_error
    
    return error


def create_session_error(
    message: str,
    session_id: Optional[str] = None,
    agent_model: Optional[str] = None,
    tool_name: Optional[str] = None,
    original_error: Optional[Exception] = None
) -> SessionError:
    """
    Factory function to create session errors with appropriate context.
    
    Args:
        message: Error message
        session_id: Session ID
        agent_model: Agent model name
        tool_name: Tool name
        original_error: Original exception
        
    Returns:
        SessionError: Configured error instance
    """
    error_code = ErrorCodes.SESSION_INIT_FAILED
    if "agent" in message.lower():
        error_code = ErrorCodes.SESSION_AGENT_ERROR
    elif "context" in message.lower():
        error_code = ErrorCodes.SESSION_CONTEXT_ERROR
    
    error = SessionError(
        message,
        session_id=session_id,
        agent_model=agent_model,
        tool_name=tool_name,
        error_code=error_code,
        original_error=original_error
    )
    
    # Set the __cause__ attribute for proper exception chaining
    if original_error:
        error.__cause__ = original_error
    
    return error