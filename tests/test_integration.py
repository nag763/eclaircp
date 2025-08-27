"""
Integration tests for complete user workflows in EclairCP.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml

from eclaircp.cli import CLIApp
from eclaircp.config import ConfigManager, MCPServerConfig, ConfigFile
from eclaircp.mcp import MCPClientManager
from eclaircp.session import SessionManager
from eclaircp.ui import ServerSelector, StreamingDisplay, StatusDisplay


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return ConfigFile(
        servers={
            "test-server": MCPServerConfig(
                name="test-server",
                command="echo",
                args=["test"],
                description="Test MCP server",
                env={"TEST_VAR": "test_value"},
                timeout=30,
                retry_attempts=3
            ),
            "another-server": MCPServerConfig(
                name="another-server",
                command="python",
                args=["-c", "print('hello')"],
                description="Another test server",
                timeout=15,
                retry_attempts=2
            )
        }
    )


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_dict = {
            'servers': {
                name: {
                    'name': server.name,
                    'command': server.command,
                    'args': server.args,
                    'description': server.description,
                    'env': server.env,
                    'timeout': server.timeout,
                    'retry_attempts': server.retry_attempts
                }
                for name, server in sample_config.servers.items()
            }
        }
        yaml.dump(config_dict, f)
        yield f.name
    
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    client = Mock(spec=MCPClientManager)
    client.connect = AsyncMock(return_value=True)
    client.disconnect = AsyncMock()
    client.is_connected = Mock(return_value=True)
    client.get_connection_status = Mock()
    client.list_tools = AsyncMock(return_value=[])
    client.get_strands_tools = Mock(return_value=[])
    return client


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing."""
    session = Mock(spec=SessionManager)
    session.start_session = AsyncMock()
    session.end_session = AsyncMock()
    session.process_input = AsyncMock()
    session.is_active = Mock(return_value=True)
    session.get_session_info = Mock(return_value={
        'active': True,
        'server_name': 'test-server',
        'model': 'test-model',
        'tools_loaded': 5,
        'mcp_connected': True,
        'connection_status': {}
    })
    return session


class TestCompleteUserWorkflow:
    """Test complete user workflow integration."""
    
    @pytest.mark.asyncio
    async def test_successful_workflow_with_server_selection(self, temp_config_file, mock_mcp_client):
        """Test complete workflow with interactive server selection."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_mcp_client), \
             patch('eclaircp.ui.ServerSelector') as mock_selector_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay'), \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=['/exit']):  # Exit immediately
            
            # Setup mocks
            mock_selector = Mock()
            mock_selector.select_server = Mock(return_value='test-server')
            mock_selector_class.return_value = mock_selector
            
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 0,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session_class.return_value = mock_session
            
            # Run the workflow
            result = await app.run(temp_config_file)
            
            # Verify workflow steps
            assert result == 0
            mock_selector.select_server.assert_called_once()
            mock_mcp_client.connect.assert_called_once()
            mock_session.start_session.assert_called_once()
            mock_session.end_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_with_specified_server(self, temp_config_file, mock_mcp_client):
        """Test workflow with pre-specified server name."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_mcp_client), \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay'), \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=['/exit']):
            
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 0,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session_class.return_value = mock_session
            
            # Run with specified server
            result = await app.run(temp_config_file, server_name='test-server')
            
            assert result == 0
            mock_mcp_client.connect.assert_called_once()
            mock_session.start_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_with_invalid_server(self, temp_config_file):
        """Test workflow with invalid server name."""
        app = CLIApp()
        
        result = await app.run(temp_config_file, server_name='nonexistent-server')
        
        assert result == 1  # Should fail
    
    @pytest.mark.asyncio
    async def test_workflow_connection_failure(self, temp_config_file):
        """Test workflow when server connection fails."""
        app = CLIApp()
        
        mock_client = Mock(spec=MCPClientManager)
        mock_client.connect = AsyncMock(return_value=False)
        mock_client.get_connection_status = Mock()
        mock_client.get_connection_status.return_value.error_message = "Connection failed"
        mock_client.is_connected = Mock(return_value=False)
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_client), \
             patch('eclaircp.ui.StatusDisplay'):
            
            result = await app.run(temp_config_file, server_name='test-server')
            
            assert result == 1  # Should fail
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, temp_config_file, mock_mcp_client):
        """Test conversation flow with streaming responses."""
        app = CLIApp()
        
        # Mock streaming events
        from eclaircp.config import StreamEvent, StreamEventType
        mock_events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="Hello"),
            StreamEvent(event_type=StreamEventType.TEXT, data=" world!"),
            StreamEvent(event_type=StreamEventType.COMPLETE, data="Done")
        ]
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_mcp_client), \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=['Hello there', '/exit']):
            
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            # Create a proper async generator mock
            async def mock_process_input(user_input):
                for event in mock_events:
                    yield event
            
            # Track calls manually
            process_input_calls = []
            async def tracked_process_input(user_input):
                process_input_calls.append(user_input)
                async for event in mock_process_input(user_input):
                    yield event
            
            mock_session.process_input = tracked_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 0,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            result = await app.run(temp_config_file, server_name='test-server')
            
            assert result == 0
            # Verify process_input was called with the right input
            assert 'Hello there' in process_input_calls
            # Verify streaming display was called for text events
            assert mock_display.stream_text_instant.call_count >= 2  # For "Hello" and " world!"
    
    @pytest.mark.asyncio
    async def test_session_commands(self, temp_config_file, mock_mcp_client):
        """Test session command handling."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_mcp_client), \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay'), \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=['/help', '/status', '/tools', '/exit']):
            
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 0,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_mcp_client
            mock_session_class.return_value = mock_session
            
            result = await app.run(temp_config_file, server_name='test-server')
            
            assert result == 0
            # Verify session info was called for /status command
            assert mock_session.get_session_info.call_count >= 2  # Once for display, once for /status
    
    @pytest.mark.asyncio
    async def test_keyboard_interrupt_handling(self, temp_config_file, mock_mcp_client):
        """Test graceful handling of keyboard interrupts."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_mcp_client), \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay'), \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=KeyboardInterrupt()):
            
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 0,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session_class.return_value = mock_session
            
            result = await app.run(temp_config_file, server_name='test-server')
            
            assert result == 0  # Should handle gracefully
            mock_session.end_session.assert_called_once()  # Should cleanup
    
    def test_list_servers_workflow(self, temp_config_file):
        """Test list servers workflow (synchronous)."""
        app = CLIApp()
        
        # This should work synchronously
        result = asyncio.run(app.run(temp_config_file, list_servers=True))
        
        assert result == 0


class TestServerSelectionFlow:
    """Test server selection flow integration."""
    
    def test_server_selector_with_single_server(self, sample_config):
        """Test server selection with only one server."""
        from eclaircp.ui import ServerSelector
        
        single_server_config = {
            "only-server": sample_config.servers["test-server"]
        }
        
        selector = ServerSelector()
        result = selector.select_server(single_server_config)
        
        assert result == "only-server"
    
    def test_server_selector_with_multiple_servers(self, sample_config):
        """Test server selection with multiple servers."""
        from eclaircp.ui import ServerSelector
        
        selector = ServerSelector()
        
        with patch.object(selector.console, 'input', return_value='1'):
            result = selector.select_server(sample_config.servers)
            assert result in sample_config.servers
        
        with patch.object(selector.console, 'input', return_value='test-server'):
            result = selector.select_server(sample_config.servers)
            assert result == 'test-server'
    
    def test_server_selector_partial_match(self, sample_config):
        """Test server selection with partial name matching."""
        from eclaircp.ui import ServerSelector
        
        selector = ServerSelector()
        
        with patch.object(selector.console, 'input', return_value='test'):
            result = selector.select_server(sample_config.servers)
            assert result == 'test-server'
    
    def test_server_selector_cancellation(self, sample_config):
        """Test server selection cancellation."""
        from eclaircp.ui import ServerSelector
        
        selector = ServerSelector()
        
        with patch.object(selector.console, 'input', return_value='quit'):
            with pytest.raises(ValueError, match="cancelled"):
                selector.select_server(sample_config.servers)


class TestConnectionFlow:
    """Test connection flow integration."""
    
    @pytest.mark.asyncio
    async def test_successful_connection_flow(self, sample_config):
        """Test successful connection establishment."""
        from eclaircp.mcp import MCPClientManager
        from eclaircp.ui import StatusDisplay
        
        client = MCPClientManager()
        status_display = StatusDisplay()
        
        # Mock the connection
        with patch.object(client, 'connect', return_value=True), \
             patch.object(client, 'get_connection_status') as mock_status, \
             patch.object(client, 'list_tools', return_value=[]):
            
            mock_status.return_value.connection_time = None
            mock_status.return_value.available_tools = []
            
            app = CLIApp()
            result = await app._handle_server_connection(
                client, 
                sample_config.servers["test-server"], 
                status_display
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_failed_connection_flow(self, sample_config):
        """Test failed connection handling."""
        from eclaircp.mcp import MCPClientManager
        from eclaircp.ui import StatusDisplay
        
        client = MCPClientManager()
        status_display = StatusDisplay()
        
        # Mock connection failure
        with patch.object(client, 'connect', side_effect=Exception("Connection failed")):
            app = CLIApp()
            result = await app._handle_server_connection(
                client, 
                sample_config.servers["test-server"], 
                status_display
            )
            
            assert result is False


class TestStreamingIntegration:
    """Test streaming response integration."""
    
    def test_stream_event_handling(self):
        """Test stream event handling in CLI."""
        from eclaircp.config import StreamEvent, StreamEventType
        from eclaircp.ui import StreamingDisplay
        
        app = CLIApp()
        display = StreamingDisplay()
        
        # Test different event types
        text_event = StreamEvent(event_type=StreamEventType.TEXT, data="Hello")
        tool_event = StreamEvent(
            event_type=StreamEventType.TOOL_USE, 
            data={
                'tool_name': 'test_tool',
                'arguments': {'arg1': 'value1'},
                'result': 'Tool result'
            }
        )
        error_event = StreamEvent(event_type=StreamEventType.ERROR, data="Error message")
        
        with patch.object(display, 'stream_text_instant') as mock_text, \
             patch.object(display, 'show_tool_usage') as mock_tool, \
             patch.object(display, 'show_tool_result') as mock_result, \
             patch.object(display, 'show_error') as mock_error:
            
            app._handle_stream_event(text_event, display)
            mock_text.assert_called_once_with("Hello")
            
            app._handle_stream_event(tool_event, display)
            mock_tool.assert_called_once_with('test_tool', {'arg1': 'value1'})
            mock_result.assert_called_once_with('test_tool', 'Tool result')
            
            app._handle_stream_event(error_event, display)
            mock_error.assert_called_once_with("Error message")


class TestErrorHandling:
    """Test error handling in integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_configuration_error_handling(self):
        """Test handling of configuration errors."""
        app = CLIApp()
        
        # Test with non-existent config file
        result = await app.run("nonexistent-config.yaml")
        assert result == 1
    
    @pytest.mark.asyncio
    async def test_session_error_handling(self, temp_config_file, mock_mcp_client):
        """Test handling of session errors."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_mcp_client), \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay'), \
             patch('eclaircp.ui.StatusDisplay'):
            
            # Mock session that fails to start
            mock_session = Mock()
            mock_session.start_session = AsyncMock(side_effect=Exception("Session failed"))
            mock_session.end_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            result = await app.run(temp_config_file, server_name='test-server')
            
            assert result == 1  # Should fail gracefully
            mock_session.end_session.assert_called_once()  # Should cleanup


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_scenario(self, temp_config_file):
        """Test a complete conversation scenario from start to finish."""
        app = CLIApp()
        
        # Mock all components for a complete flow
        mock_client = Mock(spec=MCPClientManager)
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.get_connection_status = Mock()
        mock_client.list_tools = AsyncMock(return_value=[])
        
        from eclaircp.config import StreamEvent, StreamEventType
        conversation_events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="I can help you with that."),
            StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                'tool_name': 'search_tool',
                'arguments': {'query': 'test'},
                'result': 'Search completed'
            }),
            StreamEvent(event_type=StreamEventType.TEXT, data=" Here are the results."),
            StreamEvent(event_type=StreamEventType.COMPLETE, data="Done")
        ]
        
        with patch('eclaircp.mcp.MCPClientManager', return_value=mock_client), \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=[
                 'Can you help me search for something?',
                 '/status',
                 '/exit'
             ]):
            
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            # Track calls manually for end-to-end test
            process_input_calls = []
            async def tracked_process_input(user_input):
                process_input_calls.append(user_input)
                for event in conversation_events:
                    yield event
            
            mock_session.process_input = tracked_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 1,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_client
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            result = await app.run(temp_config_file, server_name='test-server')
            
            # Verify complete workflow
            assert result == 0
            mock_client.connect.assert_called_once()
            mock_session.start_session.assert_called_once()
            # Verify process_input was called with the right input
            assert 'Can you help me search for something?' in process_input_calls
            mock_session.end_session.assert_called_once()
            mock_client.disconnect.assert_called_once()
            
            # Verify streaming display was used
            assert mock_display.stream_text_instant.call_count >= 2
            mock_display.show_tool_usage.assert_called_once()
            mock_display.show_tool_result.assert_called_once()