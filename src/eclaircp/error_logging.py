"""
EclairCP error logging utilities.

This module provides structured error logging for debugging and troubleshooting.
"""

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .exceptions import EclairCPError


class EclairCPLogger:
    """
    Structured logger for EclairCP errors and debugging information.
    """
    
    def __init__(self, log_file: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize the EclairCP logger.
        
        Args:
            log_file: Path to log file, uses stderr if None
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger("eclaircp")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add file handler if log file specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Add console handler for errors and above
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        include_traceback: bool = True
    ) -> None:
        """
        Log an error with context and traceback information.
        
        Args:
            error: Exception to log
            context: Additional context information
            include_traceback: Whether to include full traceback
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add EclairCP-specific error information
        if isinstance(error, EclairCPError):
            error_info.update({
                "error_code": error.error_code,
                "error_context": error.context,
                "error_suggestions": error.suggestions,
                "original_error": str(error.original_error) if error.original_error else None,
            })
        
        # Add additional context
        if context:
            error_info["additional_context"] = context
        
        # Add traceback if requested
        if include_traceback:
            error_info["traceback"] = traceback.format_exc()
        
        # Log the structured error information
        self.logger.error(
            "Error occurred: %s",
            error_info["error_message"],
            extra={"error_details": error_info}
        )
        
        # Log detailed information at debug level
        self.logger.debug("Full error details: %s", error_info)
    
    def log_configuration_error(
        self, 
        error: Exception, 
        config_path: Optional[str] = None,
        config_section: Optional[str] = None
    ) -> None:
        """
        Log configuration-specific errors with relevant context.
        
        Args:
            error: Configuration error
            config_path: Path to configuration file
            config_section: Configuration section that caused the error
        """
        context = {}
        if config_path:
            context["config_path"] = config_path
        if config_section:
            context["config_section"] = config_section
        
        self.log_error(error, context=context)
    
    def log_connection_error(
        self, 
        error: Exception, 
        server_name: Optional[str] = None,
        server_command: Optional[str] = None,
        connection_attempt: Optional[int] = None
    ) -> None:
        """
        Log connection-specific errors with server context.
        
        Args:
            error: Connection error
            server_name: Name of the MCP server
            server_command: Command used to start the server
            connection_attempt: Which connection attempt this was
        """
        context = {}
        if server_name:
            context["server_name"] = server_name
        if server_command:
            context["server_command"] = server_command
        if connection_attempt:
            context["connection_attempt"] = connection_attempt
        
        self.log_error(error, context=context)
    
    def log_session_error(
        self, 
        error: Exception, 
        session_id: Optional[str] = None,
        agent_model: Optional[str] = None,
        message_count: Optional[int] = None
    ) -> None:
        """
        Log session-specific errors with session context.
        
        Args:
            error: Session error
            session_id: Session identifier
            agent_model: Model being used by the agent
            message_count: Number of messages in the session
        """
        context = {}
        if session_id:
            context["session_id"] = session_id
        if agent_model:
            context["agent_model"] = agent_model
        if message_count:
            context["message_count"] = message_count
        
        self.log_error(error, context=context)
    
    def log_tool_error(
        self, 
        error: Exception, 
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        server_name: Optional[str] = None
    ) -> None:
        """
        Log tool execution errors with tool context.
        
        Args:
            error: Tool execution error
            tool_name: Name of the tool that failed
            tool_args: Arguments passed to the tool
            server_name: Name of the MCP server hosting the tool
        """
        context = {}
        if tool_name:
            context["tool_name"] = tool_name
        if tool_args:
            context["tool_args"] = tool_args
        if server_name:
            context["server_name"] = server_name
        
        self.log_error(error, context=context)
    
    def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log debug information.
        
        Args:
            message: Debug message
            context: Additional context information
        """
        if context:
            self.logger.debug("%s - Context: %s", message, context)
        else:
            self.logger.debug(message)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log informational message.
        
        Args:
            message: Info message
            context: Additional context information
        """
        if context:
            self.logger.info("%s - Context: %s", message, context)
        else:
            self.logger.info(message)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log warning message.
        
        Args:
            message: Warning message
            context: Additional context information
        """
        if context:
            self.logger.warning("%s - Context: %s", message, context)
        else:
            self.logger.warning(message)


# Global logger instance
_global_logger: Optional[EclairCPLogger] = None


def get_logger() -> EclairCPLogger:
    """
    Get the global EclairCP logger instance.
    
    Returns:
        EclairCPLogger: Global logger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = EclairCPLogger()
    return _global_logger


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> EclairCPLogger:
    """
    Set up global logging configuration.
    
    Args:
        log_file: Path to log file
        log_level: Logging level
        
    Returns:
        EclairCPLogger: Configured logger instance
    """
    global _global_logger
    _global_logger = EclairCPLogger(log_file=log_file, log_level=log_level)
    return _global_logger


def log_error(error: Exception, **kwargs) -> None:
    """
    Convenience function to log an error using the global logger.
    
    Args:
        error: Exception to log
        **kwargs: Additional arguments passed to log_error
    """
    get_logger().log_error(error, **kwargs)


def log_debug(message: str, **kwargs) -> None:
    """
    Convenience function to log debug information using the global logger.
    
    Args:
        message: Debug message
        **kwargs: Additional arguments passed to log_debug
    """
    get_logger().log_debug(message, **kwargs)


def log_info(message: str, **kwargs) -> None:
    """
    Convenience function to log info using the global logger.
    
    Args:
        message: Info message
        **kwargs: Additional arguments passed to log_info
    """
    get_logger().log_info(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """
    Convenience function to log warning using the global logger.
    
    Args:
        message: Warning message
        **kwargs: Additional arguments passed to log_warning
    """
    get_logger().log_warning(message, **kwargs)