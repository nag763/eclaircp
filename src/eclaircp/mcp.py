"""
EclairCP MCP client integration module.
"""

import asyncio
import subprocess
import time
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import MCPServerConfig, ConnectionStatus, ToolInfo


logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """MCP server connection errors."""
    pass


class MCPClientManager:
    """Manages MCP server connections and interactions."""
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self._connected_server: Optional[MCPServerConfig] = None
        self._client_session: Optional[ClientSession] = None
        self._server_process: Optional[subprocess.Popen] = None
        self._connection_status: ConnectionStatus = ConnectionStatus(
            server_name="", connected=False
        )
        self._available_tools: List[ToolInfo] = []
    
    async def connect(self, config: MCPServerConfig) -> bool:
        """
        Establish connection to MCP server with timeout and retry logic.
        
        Args:
            config: Server configuration
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection fails after all retries
        """
        if self._client_session and self._connection_status.connected:
            await self.disconnect()
        
        last_error = None
        
        for attempt in range(config.retry_attempts):
            try:
                logger.info(f"Attempting to connect to {config.name} (attempt {attempt + 1}/{config.retry_attempts})")
                
                # Create server parameters
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env if config.env else None
                )
                
                # Start the server process and create client session
                async with stdio_client(server_params) as (read, write):
                    self._client_session = ClientSession(read, write)
                    
                    # Initialize the session with timeout
                    try:
                        await asyncio.wait_for(
                            self._client_session.initialize(),
                            timeout=config.timeout
                        )
                    except asyncio.TimeoutError:
                        raise ConnectionError(f"Connection timeout after {config.timeout} seconds")
                    
                    # Test the connection by listing tools
                    tools_response = await self._client_session.list_tools()
                    
                    # Update connection status
                    self._connected_server = config
                    self._connection_status = ConnectionStatus(
                        server_name=config.name,
                        connected=True,
                        connection_time=datetime.now(),
                        available_tools=[tool.name for tool in tools_response.tools]
                    )
                    
                    # Cache available tools
                    self._available_tools = [
                        ToolInfo(
                            name=tool.name,
                            description=tool.description or "",
                            parameters=tool.inputSchema.model_dump() if tool.inputSchema else {}
                        )
                        for tool in tools_response.tools
                    ]
                    
                    logger.info(f"Successfully connected to {config.name} with {len(self._available_tools)} tools")
                    return True
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < config.retry_attempts - 1:
                    # Wait before retrying (exponential backoff)
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        # All attempts failed
        error_msg = f"Failed to connect to {config.name} after {config.retry_attempts} attempts: {last_error}"
        self._connection_status = ConnectionStatus(
            server_name=config.name,
            connected=False,
            error_message=str(last_error)
        )
        
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    async def disconnect(self) -> None:
        """Close MCP server connection and cleanup resources."""
        if self._client_session:
            try:
                # Close the client session
                await self._client_session.close()
                logger.info(f"Disconnected from {self._connected_server.name if self._connected_server else 'server'}")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._client_session = None
        
        # Clean up server process if it exists
        if self._server_process:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._server_process.kill()
            except Exception as e:
                logger.warning(f"Error terminating server process: {e}")
            finally:
                self._server_process = None
        
        # Reset connection status
        self._connected_server = None
        self._connection_status = ConnectionStatus(
            server_name="", connected=False
        )
        self._available_tools = []
    
    def get_connection_status(self) -> ConnectionStatus:
        """
        Get current connection status.
        
        Returns:
            ConnectionStatus object with current connection information
        """
        return self._connection_status
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to an MCP server.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connection_status.connected and self._client_session is not None
    
    async def list_tools(self) -> List[ToolInfo]:
        """
        Get available tools from connected server.
        
        Returns:
            List of ToolInfo objects describing available tools
            
        Raises:
            ConnectionError: If not connected to a server
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to any MCP server")
        
        return self._available_tools.copy()
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the connected MCP server.
        
        Args:
            name: Tool name to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ConnectionError: If not connected to a server
            ValueError: If tool name is invalid
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to any MCP server")
        
        if not self._client_session:
            raise ConnectionError("Client session is not available")
        
        # Verify tool exists
        tool_names = [tool.name for tool in self._available_tools]
        if name not in tool_names:
            raise ValueError(f"Tool '{name}' not found. Available tools: {tool_names}")
        
        try:
            logger.info(f"Calling tool '{name}' with arguments: {arguments}")
            result = await self._client_session.call_tool(name, arguments)
            logger.info(f"Tool '{name}' executed successfully")
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error calling tool '{name}': {e}")
            raise ConnectionError(f"Tool execution failed: {e}") from e
    
    def get_strands_tools(self) -> List[Callable]:
        """
        Convert MCP tools to Strands-compatible tools.
        
        Returns:
            List of Strands-compatible tool functions
            
        Raises:
            ConnectionError: If not connected to a server
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to any MCP server")
        
        proxy = MCPToolProxy(self)
        return [proxy.create_strands_tool(tool) for tool in self._available_tools]


class MCPToolProxy:
    """Proxy for MCP tools to integrate with Strands."""
    
    def __init__(self, mcp_client: MCPClientManager):
        """
        Initialize the tool proxy.
        
        Args:
            mcp_client: MCP client manager instance
        """
        self.mcp_client = mcp_client
    
    def create_strands_tool(self, tool_info: ToolInfo) -> Callable:
        """
        Create a Strands-compatible tool from MCP tool definition.
        
        Args:
            tool_info: ToolInfo object with tool metadata
            
        Returns:
            Strands-compatible tool function
        """
        from strands import tool
        
        # Create the tool function dynamically
        async def mcp_tool_wrapper(**kwargs) -> str:
            """
            Dynamically created wrapper for MCP tool.
            
            This function calls the MCP tool with the provided arguments
            and returns the result as a string.
            """
            try:
                # Call the MCP tool through the client manager
                result = await self.mcp_client.call_tool(tool_info.name, kwargs)
                
                # Convert result to string for Strands compatibility
                if isinstance(result, dict):
                    # If result has content field, use that
                    if 'content' in result:
                        content = result['content']
                        if isinstance(content, list):
                            # Handle list of content items (common in MCP responses)
                            return '\n'.join(str(item.get('text', item)) if isinstance(item, dict) else str(item) for item in content)
                        return str(content)
                    # Otherwise, format the entire result
                    return str(result)
                
                return str(result)
                
            except Exception as e:
                logger.error(f"Error executing MCP tool '{tool_info.name}': {e}")
                return f"Error executing tool '{tool_info.name}': {str(e)}"
        
        # Set function metadata for Strands
        mcp_tool_wrapper.__name__ = tool_info.name
        mcp_tool_wrapper.__doc__ = tool_info.description or f"MCP tool: {tool_info.name}"
        
        # Add parameter annotations based on tool schema
        if tool_info.parameters and 'properties' in tool_info.parameters:
            # Create annotations from JSON schema
            annotations = {}
            properties = tool_info.parameters['properties']
            required_fields = tool_info.parameters.get('required', [])
            
            for param_name, param_info in properties.items():
                param_type = self._json_schema_to_python_type(param_info)
                
                # Make optional parameters Optional[type]
                if param_name not in required_fields:
                    from typing import Optional
                    param_type = Optional[param_type]
                
                annotations[param_name] = param_type
            
            # Set return type annotation
            annotations['return'] = str
            mcp_tool_wrapper.__annotations__ = annotations
        
        # Apply the Strands tool decorator
        return tool(mcp_tool_wrapper)
    
    def _json_schema_to_python_type(self, schema: Dict[str, Any]) -> type:
        """
        Convert JSON schema type to Python type annotation.
        
        Args:
            schema: JSON schema property definition
            
        Returns:
            Python type for annotation
        """
        schema_type = schema.get('type', 'string')
        
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        
        return type_mapping.get(schema_type, str)