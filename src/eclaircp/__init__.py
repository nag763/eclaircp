"""
EclairCP - Elegant CLI for testing MCP servers.

A Python-based tool for interactive testing and validation of Model Context Protocol 
servers with streaming responses powered by Strands agents.
"""

__version__ = "0.1.0"
__author__ = "Loïc"
__email__ = "loic.labeye@tutanota.de"
__license__ = "MIT"

from .cli import main
from .config import MCPServerConfig, SessionConfig, ConfigFile, ConfigManager
from .mcp import MCPClientManager, MCPToolProxy
from .session import SessionManager, StreamingHandler
from .ui import StreamingDisplay, ServerSelector, StatusDisplay
from .exceptions import (
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
from .error_logging import (
    EclairCPLogger,
    get_logger,
    setup_logging,
    log_error,
    log_debug,
    log_info,
    log_warning,
)

__all__ = [
    "main",
    "MCPServerConfig",
    "SessionConfig", 
    "ConfigFile",
    "ConfigManager",
    "MCPClientManager",
    "MCPToolProxy",
    "SessionManager",
    "StreamingHandler",
    "StreamingDisplay",
    "ServerSelector",
    "StatusDisplay",
    "EclairCPError",
    "ConfigurationError",
    "ConnectionError",
    "SessionError",
    "ToolExecutionError",
    "ValidationError",
    "UserInterruptError",
    "ErrorCodes",
    "create_configuration_error",
    "create_connection_error",
    "create_session_error",
    "EclairCPLogger",
    "get_logger",
    "setup_logging",
    "log_error",
    "log_debug",
    "log_info",
    "log_warning",
]
