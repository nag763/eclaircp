"""
Tests for the MCP client module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from eclaircp.mcp import MCPClientManager, MCPToolProxy, ConnectionError
from eclaircp.config import MCPServerConfig, ConnectionStatus, ToolInfo


@pytest.fixture
def sample_config():
    """Create a sample MCP server configuration for testing."""
    return MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-package"],
        description="Test MCP server",
        timeout=10,
        retry_attempts=2
    )


@pytest.fixture
def mcp_manager():
    """Create an MCPClientManager instance for testing."""
    return MCPClientManager()


class TestMCPClientManager:
    """Test cases for MCPClientManager."""
    
    def test_initialization(self, mcp_manager):
        """Test MCPClientManager initialization."""
        assert mcp_manager._connected_server is None
        assert mcp_manager._client_session is None
        assert mcp_manager._server_process is None
        assert not mcp_manager._connection_status.connected
        assert mcp_manager._connection_status.server_name == ""
        assert mcp_manager._available_tools == []
    
    def test_is_connected_false_initially(self, mcp_manager):
        """Test that is_connected returns False initially."""
        assert not mcp_manager.is_connected()
    
    def test_get_connection_status_initial(self, mcp_manager):
        """Test getting initial connection status."""
        status = mcp_manager.get_connection_status()
        assert isinstance(status, ConnectionStatus)
        assert not status.connected
        assert status.server_name == ""
        assert status.connection_time is None
        assert status.error_message is None
        assert status.available_tools == []
    
    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self, mcp_manager):
        """Test that list_tools raises ConnectionError when not connected."""
        with pytest.raises(ConnectionError, match="Not connected to any MCP server"):
            await mcp_manager.list_tools()
    
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, mcp_manager):
        """Test that call_tool raises ConnectionError when not connected."""
        with pytest.raises(ConnectionError, match="Not connected to any MCP server"):
            await mcp_manager.call_tool("test_tool", {})
    
    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, mcp_manager):
        """Test that disconnect works safely when not connected."""
        # Should not raise any exceptions
        await mcp_manager.disconnect()
        assert not mcp_manager.is_connected()
    
    @pytest.mark.asyncio
    @patch('eclaircp.mcp.stdio_client')
    async def test_connect_success(self, mock_stdio_client, mcp_manager, sample_config):
        """Test successful connection to MCP server."""
        # Mock the stdio client context manager
        mock_read = Mock()
        mock_write = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = (mock_read, mock_write)
        mock_context.__aexit__.return_value = None
        mock_stdio_client.return_value = mock_context
        
        # Mock the client session
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        
        # Mock tools response
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool description"
        mock_tool.inputSchema = Mock()
        mock_tool.inputSchema.model_dump.return_value = {"type": "object"}
        
        mock_tools_response = Mock()
        mock_tools_response.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_tools_response
        
        with patch('eclaircp.mcp.ClientSession', return_value=mock_session):
            result = await mcp_manager.connect(sample_config)
            
            assert result is True
            assert mcp_manager.is_connected()
            assert mcp_manager._connected_server == sample_config
            
            status = mcp_manager.get_connection_status()
            assert status.connected
            assert status.server_name == "test-server"
            assert status.connection_time is not None
            assert status.available_tools == ["test_tool"]
            assert len(mcp_manager._available_tools) == 1
            assert mcp_manager._available_tools[0].name == "test_tool"
    
    @pytest.mark.asyncio
    @patch('eclaircp.mcp.stdio_client')
    async def test_connect_timeout(self, mock_stdio_client, mcp_manager, sample_config):
        """Test connection timeout handling."""
        # Mock the stdio client context manager
        mock_read = Mock()
        mock_write = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = (mock_read, mock_write)
        mock_context.__aexit__.return_value = None
        mock_stdio_client.return_value = mock_context
        
        # Mock the client session with timeout
        mock_session = AsyncMock()
        mock_session.initialize.side_effect = asyncio.TimeoutError()
        
        with patch('eclaircp.mcp.ClientSession', return_value=mock_session):
            with pytest.raises(ConnectionError, match="Connection timeout after 10 seconds"):
                await mcp_manager.connect(sample_config)
            
            assert not mcp_manager.is_connected()
            status = mcp_manager.get_connection_status()
            assert not status.connected
            assert "Connection timeout" in status.error_message
    
    @pytest.mark.asyncio
    @patch('eclaircp.mcp.stdio_client')
    async def test_connect_retry_logic(self, mock_stdio_client, mcp_manager, sample_config):
        """Test connection retry logic with eventual success."""
        # Mock the stdio client context manager
        mock_read = Mock()
        mock_write = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = (mock_read, mock_write)
        mock_context.__aexit__.return_value = None
        mock_stdio_client.return_value = mock_context
        
        # Mock the client session - fail first attempt, succeed second
        mock_session = AsyncMock()
        mock_session.initialize.side_effect = [
            Exception("First attempt fails"),
            None  # Second attempt succeeds
        ]
        
        # Mock tools response for successful attempt
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.inputSchema = None
        
        mock_tools_response = Mock()
        mock_tools_response.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_tools_response
        
        with patch('eclaircp.mcp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep'):  # Speed up the test
                result = await mcp_manager.connect(sample_config)
                
                assert result is True
                assert mcp_manager.is_connected()
                # Verify initialize was called twice (retry logic)
                assert mock_session.initialize.call_count == 2
    
    @pytest.mark.asyncio
    @patch('eclaircp.mcp.stdio_client')
    async def test_connect_all_retries_fail(self, mock_stdio_client, mcp_manager, sample_config):
        """Test connection failure after all retries."""
        # Mock the stdio client context manager
        mock_read = Mock()
        mock_write = Mock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = (mock_read, mock_write)
        mock_context.__aexit__.return_value = None
        mock_stdio_client.return_value = mock_context
        
        # Mock the client session to always fail
        mock_session = AsyncMock()
        mock_session.initialize.side_effect = Exception("Connection failed")
        
        with patch('eclaircp.mcp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep'):  # Speed up the test
                with pytest.raises(ConnectionError, match="Failed to connect to test-server after 2 attempts"):
                    await mcp_manager.connect(sample_config)
                
                assert not mcp_manager.is_connected()
                status = mcp_manager.get_connection_status()
                assert not status.connected
                assert "Connection failed" in status.error_message
    
    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, mcp_manager):
        """Test proper cleanup during disconnect."""
        # Set up a mock connected state
        mock_session = AsyncMock()
        mock_process = Mock()
        mock_config = Mock()
        mock_config.name = "test-server"
        
        mcp_manager._client_session = mock_session
        mcp_manager._server_process = mock_process
        mcp_manager._connected_server = mock_config
        mcp_manager._connection_status = ConnectionStatus(
            server_name="test-server", connected=True
        )
        mcp_manager._available_tools = [ToolInfo(name="test", description="test")]
        
        await mcp_manager.disconnect()
        
        # Verify cleanup
        mock_session.close.assert_called_once()
        assert mcp_manager._client_session is None
        assert mcp_manager._server_process is None
        assert mcp_manager._connected_server is None
        assert not mcp_manager._connection_status.connected
        assert mcp_manager._available_tools == []
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_manager):
        """Test successful tool execution."""
        # Set up connected state
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_session.call_tool.return_value = mock_result
        
        mcp_manager._client_session = mock_session
        mcp_manager._connection_status = ConnectionStatus(
            server_name="test-server", connected=True
        )
        mcp_manager._available_tools = [
            ToolInfo(name="test_tool", description="Test tool")
        ]
        
        result = await mcp_manager.call_tool("test_tool", {"arg": "value"})
        
        assert result == {"result": "success"}
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})
    
    @pytest.mark.asyncio
    async def test_call_tool_invalid_name(self, mcp_manager):
        """Test calling non-existent tool."""
        # Set up connected state
        mock_session = AsyncMock()
        mcp_manager._client_session = mock_session
        mcp_manager._connection_status = ConnectionStatus(
            server_name="test-server", connected=True
        )
        mcp_manager._available_tools = [
            ToolInfo(name="valid_tool", description="Valid tool")
        ]
        
        with pytest.raises(ValueError, match="Tool 'invalid_tool' not found"):
            await mcp_manager.call_tool("invalid_tool", {})
    
    @pytest.mark.asyncio
    async def test_call_tool_execution_error(self, mcp_manager):
        """Test tool execution error handling."""
        # Set up connected state
        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = Exception("Tool execution failed")
        
        mcp_manager._client_session = mock_session
        mcp_manager._connection_status = ConnectionStatus(
            server_name="test-server", connected=True
        )
        mcp_manager._available_tools = [
            ToolInfo(name="test_tool", description="Test tool")
        ]
        
        with pytest.raises(ConnectionError, match="Tool execution failed"):
            await mcp_manager.call_tool("test_tool", {})


    @pytest.mark.asyncio
    async def test_get_strands_tools_not_connected(self, mcp_manager):
        """Test that get_strands_tools raises ConnectionError when not connected."""
        with pytest.raises(ConnectionError, match="Not connected to any MCP server"):
            mcp_manager.get_strands_tools()
    
    @pytest.mark.asyncio
    async def test_get_strands_tools_success(self, mcp_manager):
        """Test successful conversion of MCP tools to Strands tools."""
        # Set up connected state with tools
        mock_session = AsyncMock()
        mcp_manager._client_session = mock_session
        mcp_manager._connection_status = ConnectionStatus(
            server_name="test-server", connected=True
        )
        mcp_manager._available_tools = [
            ToolInfo(
                name="test_tool",
                description="Test tool description",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            )
        ]
        
        with patch('strands.tool') as mock_tool_decorator:
            # Mock the tool decorator to return the function as-is
            mock_tool_decorator.side_effect = lambda f: f
            
            tools = mcp_manager.get_strands_tools()
            
            assert len(tools) == 1
            assert callable(tools[0])
            mock_tool_decorator.assert_called_once()


class TestMCPToolProxy:
    """Test cases for MCPToolProxy."""
    
    def test_initialization(self, mcp_manager):
        """Test MCPToolProxy initialization."""
        proxy = MCPToolProxy(mcp_manager)
        assert proxy.mcp_client is mcp_manager
    
    @patch('strands.tool')
    def test_create_strands_tool_basic(self, mock_tool_decorator, mcp_manager):
        """Test creating a basic Strands tool from MCP tool info."""
        mock_tool_decorator.side_effect = lambda f: f  # Return function as-is
        
        proxy = MCPToolProxy(mcp_manager)
        tool_info = ToolInfo(
            name="test_tool",
            description="Test tool description",
            parameters={}
        )
        
        result = proxy.create_strands_tool(tool_info)
        
        assert callable(result)
        assert result.__name__ == "test_tool"
        assert result.__doc__ == "Test tool description"
        mock_tool_decorator.assert_called_once()
    
    @patch('strands.tool')
    def test_create_strands_tool_with_parameters(self, mock_tool_decorator, mcp_manager):
        """Test creating a Strands tool with parameter annotations."""
        mock_tool_decorator.side_effect = lambda f: f  # Return function as-is
        
        proxy = MCPToolProxy(mcp_manager)
        tool_info = ToolInfo(
            name="search_tool",
            description="Search for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Result limit"}
                },
                "required": ["query"]
            }
        )
        
        result = proxy.create_strands_tool(tool_info)
        
        assert callable(result)
        assert result.__name__ == "search_tool"
        assert result.__doc__ == "Search for information"
        
        # Check annotations
        annotations = result.__annotations__
        assert 'query' in annotations
        assert 'limit' in annotations
        assert annotations['return'] == str
        
        mock_tool_decorator.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('strands.tool')
    async def test_tool_wrapper_execution_success(self, mock_tool_decorator, mcp_manager):
        """Test successful execution of wrapped MCP tool."""
        # Mock the tool decorator to return the function as-is
        mock_tool_decorator.side_effect = lambda f: f
        
        # Mock successful tool call
        mcp_manager.call_tool = AsyncMock(return_value={
            "content": [{"text": "Tool execution result"}]
        })
        
        proxy = MCPToolProxy(mcp_manager)
        tool_info = ToolInfo(name="test_tool", description="Test tool")
        
        wrapped_tool = proxy.create_strands_tool(tool_info)
        result = await wrapped_tool(query="test")
        
        assert result == "Tool execution result"
        mcp_manager.call_tool.assert_called_once_with("test_tool", {"query": "test"})
    
    @pytest.mark.asyncio
    @patch('strands.tool')
    async def test_tool_wrapper_execution_error(self, mock_tool_decorator, mcp_manager):
        """Test error handling in wrapped MCP tool."""
        # Mock the tool decorator to return the function as-is
        mock_tool_decorator.side_effect = lambda f: f
        
        # Mock tool call failure
        mcp_manager.call_tool = AsyncMock(side_effect=Exception("Tool failed"))
        
        proxy = MCPToolProxy(mcp_manager)
        tool_info = ToolInfo(name="test_tool", description="Test tool")
        
        wrapped_tool = proxy.create_strands_tool(tool_info)
        result = await wrapped_tool(query="test")
        
        assert "Error executing tool 'test_tool': Tool failed" in result
    
    def test_json_schema_to_python_type(self, mcp_manager):
        """Test JSON schema to Python type conversion."""
        proxy = MCPToolProxy(mcp_manager)
        
        # Test various schema types
        assert proxy._json_schema_to_python_type({"type": "string"}) == str
        assert proxy._json_schema_to_python_type({"type": "integer"}) == int
        assert proxy._json_schema_to_python_type({"type": "number"}) == float
        assert proxy._json_schema_to_python_type({"type": "boolean"}) == bool
        assert proxy._json_schema_to_python_type({"type": "array"}) == list
        assert proxy._json_schema_to_python_type({"type": "object"}) == dict
        
        # Test unknown type defaults to str
        assert proxy._json_schema_to_python_type({"type": "unknown"}) == str
        assert proxy._json_schema_to_python_type({}) == str


class TestMCPIntegration:
    """Integration tests for MCP client functionality."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """Test the complete workflow from connection to tool execution."""
        # Create a manager and config
        manager = MCPClientManager()
        config = MCPServerConfig(
            name="test-integration",
            command="uvx",
            args=["test-mcp-server"],
            timeout=5,
            retry_attempts=1
        )
        
        # Mock the entire MCP client workflow
        with patch('eclaircp.mcp.stdio_client') as mock_stdio_client:
            # Mock stdio client context manager
            mock_read = Mock()
            mock_write = Mock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = (mock_read, mock_write)
            mock_context.__aexit__.return_value = None
            mock_stdio_client.return_value = mock_context
            
            # Mock client session
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            
            # Mock tool definition
            mock_tool = Mock()
            mock_tool.name = "search"
            mock_tool.description = "Search for information"
            mock_tool.inputSchema = Mock()
            mock_tool.inputSchema.model_dump.return_value = {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
            
            mock_tools_response = Mock()
            mock_tools_response.tools = [mock_tool]
            mock_session.list_tools.return_value = mock_tools_response
            
            # Mock tool execution
            mock_session.call_tool.return_value = Mock(
                model_dump=lambda: {"content": [{"text": "Search results"}]}
            )
            
            with patch('eclaircp.mcp.ClientSession', return_value=mock_session):
                with patch('strands.tool') as mock_tool_decorator:
                    mock_tool_decorator.side_effect = lambda f: f
                    
                    # Test the complete workflow
                    # 1. Connect to server
                    success = await manager.connect(config)
                    assert success
                    assert manager.is_connected()
                    
                    # 2. List available tools
                    tools = await manager.list_tools()
                    assert len(tools) == 1
                    assert tools[0].name == "search"
                    
                    # 3. Get Strands-compatible tools
                    strands_tools = manager.get_strands_tools()
                    assert len(strands_tools) == 1
                    assert callable(strands_tools[0])
                    
                    # 4. Execute a tool
                    result = await manager.call_tool("search", {"query": "test"})
                    assert result["content"][0]["text"] == "Search results"
                    
                    # 5. Execute via Strands wrapper
                    wrapped_result = await strands_tools[0](query="test")
                    assert wrapped_result == "Search results"
                    
                    # 6. Disconnect
                    await manager.disconnect()
                    assert not manager.is_connected()