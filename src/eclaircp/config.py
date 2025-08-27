"""
EclairCP configuration management module.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, field_serializer


class MCPServerConfig(BaseModel):
    """Configuration for an individual MCP server."""
    
    name: str
    command: str
    args: List[str]
    description: str = ""
    env: Dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        """Validate that command is not empty and strip whitespace."""
        if not v.strip():
            raise ValueError('Command cannot be empty')
        return v.strip()

    @field_validator('args')
    @classmethod
    def validate_args(cls, v):
        """Strip whitespace from arguments and remove empty ones."""
        return [arg.strip() for arg in v if arg.strip()]


class SessionConfig(BaseModel):
    """Configuration for session management."""
    
    server_name: str
    model: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    system_prompt: str = "You are a helpful assistant for testing MCP servers."
    max_context_length: int = Field(default=100000, ge=1000, le=1000000)
    
    @field_validator('server_name')
    @classmethod
    def validate_server_name(cls, v):
        """Validate that server name is not empty and strip whitespace."""
        if not v.strip():
            raise ValueError('Server name cannot be empty')
        return v.strip()


class ConfigFile(BaseModel):
    """Main configuration file structure."""
    
    servers: Dict[str, MCPServerConfig]
    default_session: Optional[SessionConfig] = None
    
    @field_validator('servers')
    @classmethod
    def validate_servers(cls, v):
        """Validate that at least one server is configured."""
        if not v:
            raise ValueError('At least one server must be configured')
        return v


class ConnectionStatus(BaseModel):
    """Runtime status of MCP server connection."""
    
    server_name: str
    connected: bool
    connection_time: Optional[datetime] = None
    error_message: Optional[str] = None
    available_tools: List[str] = Field(default_factory=list)
    
    @field_serializer('connection_time')
    def serialize_connection_time(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return value.isoformat() if value else None


class StreamEventType(str, Enum):
    """Types of streaming events."""
    
    TEXT = "text"
    TOOL_USE = "tool_use"
    ERROR = "error"
    COMPLETE = "complete"
    STATUS = "status"


class StreamEvent(BaseModel):
    """Streaming event data structure."""
    
    event_type: StreamEventType
    data: Any
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()


class ToolInfo(BaseModel):
    """Information about an available MCP tool."""
    
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate that tool name is not empty."""
        if not v.strip():
            raise ValueError('Tool name cannot be empty')
        return v.strip()


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class ConfigManager:
    """Manages configuration file loading, parsing, and validation."""

    def load_config(self, path: str) -> ConfigFile:
        """Load and parse configuration file using Pydantic validation.
        
        Args:
            path: Path to the YAML configuration file
            
        Returns:
            ConfigFile: Validated configuration object
            
        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
        """
        import yaml
        import os
        
        if not os.path.exists(path):
            raise ConfigurationError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
        except IOError as e:
            raise ConfigurationError(f"Cannot read configuration file: {e}") from e
        
        if config_data is None:
            raise ConfigurationError("Configuration file is empty")
        
        return self.validate_config(config_data)

    def save_config(self, config: ConfigFile, path: str) -> None:
        """Save configuration file with Pydantic serialization.
        
        Args:
            config: Configuration object to save
            path: Path where to save the YAML configuration file
            
        Raises:
            ConfigurationError: If file cannot be saved
        """
        import yaml
        import os
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
            config_data = config.model_dump(exclude_none=True)
            with open(path, 'w', encoding='utf-8') as file:
                yaml.dump(config_data, file, default_flow_style=False, indent=2)
        except IOError as e:
            raise ConfigurationError(f"Cannot write configuration file: {e}") from e

    def validate_config(self, config_data: Dict) -> ConfigFile:
        """Validate configuration using Pydantic models.
        
        Args:
            config_data: Raw configuration data dictionary
            
        Returns:
            ConfigFile: Validated configuration object
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Convert server configurations to MCPServerConfig objects
            if 'servers' in config_data:
                servers = {}
                for name, server_data in config_data['servers'].items():
                    # Add the name to the server data
                    server_data_with_name = dict(server_data)
                    server_data_with_name['name'] = name
                    servers[name] = MCPServerConfig(**server_data_with_name)
                config_data['servers'] = servers
            
            return ConfigFile(**config_data)
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}") from e