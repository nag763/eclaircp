"""
EclairCP configuration management module.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


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
        if not v.strip():
            raise ValueError('Command cannot be empty')
        return v.strip()
    
    @field_validator('args')
    @classmethod
    def validate_args(cls, v):
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
        if not v:
            raise ValueError('At least one server must be configured')
        return v


class ConfigManager:
    """Manages configuration file loading, parsing, and validation."""
    
    def load_config(self, path: str) -> ConfigFile:
        """Load and parse configuration file using Pydantic validation."""
        # Placeholder - will be implemented in task 2.2
        raise NotImplementedError("Configuration loading will be implemented in task 2.2")
    
    def save_config(self, config: ConfigFile, path: str) -> None:
        """Save configuration file with Pydantic serialization."""
        # Placeholder - will be implemented in task 2.2
        raise NotImplementedError("Configuration saving will be implemented in task 2.2")
    
    def validate_config(self, config_data: Dict) -> ConfigFile:
        """Validate configuration using Pydantic models."""
        # Placeholder - will be implemented in task 2.2
        raise NotImplementedError("Configuration validation will be implemented in task 2.2")