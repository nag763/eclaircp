"""
EclairCP user interface components module.
"""

from typing import Dict
from .config import MCPServerConfig


class StreamingDisplay:
    """Real-time response rendering with Rich formatting."""
    
    def __init__(self):
        """Initialize the streaming display."""
        pass
    
    def stream_text(self, text: str) -> None:
        """
        Display streaming text with formatting.
        
        Args:
            text: Text to display
        """
        # Placeholder - will be implemented in task 6.1
        raise NotImplementedError("Text streaming will be implemented in task 6.1")
    
    def show_tool_usage(self, tool_name: str, args: Dict) -> None:
        """
        Display tool execution information.
        
        Args:
            tool_name: Name of the tool being used
            args: Tool arguments
        """
        # Placeholder - will be implemented in task 6.1
        raise NotImplementedError("Tool usage display will be implemented in task 6.1")
    
    def show_error(self, error: str) -> None:
        """
        Display error messages with formatting.
        
        Args:
            error: Error message to display
        """
        # Placeholder - will be implemented in task 6.1
        raise NotImplementedError("Error display will be implemented in task 6.1")


class ServerSelector:
    """Interactive server selection interface using Textual."""
    
    def __init__(self):
        """Initialize the server selector."""
        pass
    
    def select_server(self, servers: Dict[str, MCPServerConfig]) -> str:
        """
        Interactive server selection interface.
        
        Args:
            servers: Available server configurations
            
        Returns:
            Selected server name
        """
        # Placeholder - will be implemented in task 6.2
        raise NotImplementedError("Server selection will be implemented in task 6.2")


class StatusDisplay:
    """Connection and operation status display."""
    
    def __init__(self):
        """Initialize the status display."""
        pass
    
    def show_connection_status(self, server_name: str, connected: bool) -> None:
        """
        Display connection status.
        
        Args:
            server_name: Name of the server
            connected: Connection status
        """
        # Placeholder - will be implemented in task 6.2
        raise NotImplementedError("Status display will be implemented in task 6.2")