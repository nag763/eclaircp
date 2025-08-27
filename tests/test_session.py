"""
Tests for the session management module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from eclaircp.session import SessionManager, StreamingHandler
from eclaircp.mcp import MCPClientManager
from eclaircp.config import SessionConfig, StreamEvent, StreamEventType, ToolInfo


class TestSessionManager:
    """Test cases for SessionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mcp_client = Mock(spec=MCPClientManager)
        self.session_config = SessionConfig(server_name="test_server")
        self.session_manager = SessionManager(self.mcp_client, self.session_config)
    
    def test_initialization(self):
        """Test SessionManager initialization."""
        assert self.session_manager.mcp_client is self.mcp_client
        assert self.session_manager.session_config == self.session_config
        assert not self.session_manager._session_active
        assert self.session_manager._agent is None
        assert self.session_manager._tools == []
    
    def test_initialization_with_default_config(self):
        """Test SessionManager initialization with default config."""
        session = SessionManager(self.mcp_client)
        assert session.session_config.server_name == "default"
        assert session.session_config.model == "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    
    @pytest.mark.asyncio
    async def test_start_session_success(self):
        """Test successful session start."""
        # Mock MCP client
        self.mcp_client.is_connected.return_value = True
        mock_tools = [Mock(), Mock()]
        self.mcp_client.get_strands_tools.return_value = mock_tools
        
        # Mock Strands Agent
        with patch('eclaircp.session.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            await self.session_manager.start_session()
            
            # Verify session state
            assert self.session_manager._session_active
            assert self.session_manager._agent is mock_agent
            assert self.session_manager._tools == mock_tools
            assert self.session_manager._streaming_handler is not None
            
            # Verify Agent was initialized correctly
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['system_prompt'] == self.session_config.system_prompt
            assert call_kwargs['tools'] == mock_tools
            assert call_kwargs['max_context_length'] == self.session_config.max_context_length
    
    @pytest.mark.asyncio
    async def test_start_session_not_connected(self):
        """Test session start when MCP client is not connected."""
        self.mcp_client.is_connected.return_value = False
        
        with pytest.raises(RuntimeError, match="MCP client is not connected"):
            await self.session_manager.start_session()
        
        assert not self.session_manager._session_active
    
    @pytest.mark.asyncio
    async def test_start_session_already_active(self):
        """Test starting session when already active."""
        self.session_manager._session_active = True
        
        # Should not raise an error, just log a warning
        await self.session_manager.start_session()
        
        # Session should remain active
        assert self.session_manager._session_active
    
    @pytest.mark.asyncio
    async def test_start_session_agent_initialization_failure(self):
        """Test session start when agent initialization fails."""
        self.mcp_client.is_connected.return_value = True
        self.mcp_client.get_strands_tools.return_value = []
        
        with patch('eclaircp.session.Agent', side_effect=Exception("Agent init failed")):
            with pytest.raises(RuntimeError, match="Failed to start session"):
                await self.session_manager.start_session()
            
            assert not self.session_manager._session_active
    
    @pytest.mark.asyncio
    async def test_process_input_success(self):
        """Test successful input processing."""
        # Set up active session
        self.session_manager._session_active = True
        mock_agent = AsyncMock()
        self.session_manager._agent = mock_agent
        
        # Mock agent stream response
        async def mock_stream():
            yield Mock(type='text', text='Hello')
            yield Mock(type='text', text=' world')
        
        # Create a proper async iterator mock
        mock_agent.stream_async = Mock(return_value=mock_stream())
        
        # Process input
        events = []
        async for event in self.session_manager.process_input("test input"):
            events.append(event)
        
        # Verify events
        assert len(events) >= 3  # status, text events, complete
        assert events[0].event_type == StreamEventType.STATUS
        assert events[-1].event_type == StreamEventType.COMPLETE
        
        # Verify agent was called
        mock_agent.stream_async.assert_called_once_with("test input")
    
    @pytest.mark.asyncio
    async def test_process_input_session_not_active(self):
        """Test input processing when session is not active."""
        with pytest.raises(RuntimeError, match="Session is not active"):
            async for event in self.session_manager.process_input("test"):
                pass
    
    @pytest.mark.asyncio
    async def test_process_input_empty_input(self):
        """Test input processing with empty input."""
        self.session_manager._session_active = True
        self.session_manager._agent = Mock()
        
        events = []
        async for event in self.session_manager.process_input("   "):
            events.append(event)
        
        assert len(events) == 1
        assert events[0].event_type == StreamEventType.ERROR
        assert "Empty input provided" in events[0].data
    
    @pytest.mark.asyncio
    async def test_process_input_agent_error(self):
        """Test input processing when agent raises an error."""
        self.session_manager._session_active = True
        mock_agent = AsyncMock()
        async def mock_stream_error():
            raise Exception("Agent error")
        
        mock_agent.stream_async = Mock(return_value=mock_stream_error())
        self.session_manager._agent = mock_agent
        
        events = []
        async for event in self.session_manager.process_input("test"):
            events.append(event)
        
        # Should have status and error events
        assert len(events) >= 2
        assert events[0].event_type == StreamEventType.STATUS
        error_events = [e for e in events if e.event_type == StreamEventType.ERROR]
        assert len(error_events) >= 1
        assert "Error processing input" in error_events[0].data
    
    def test_convert_strands_event_text(self):
        """Test converting Strands text event."""
        mock_event = Mock(type='text', text='Hello world')
        
        result = asyncio.run(self.session_manager._convert_strands_event(mock_event))
        
        assert result.event_type == StreamEventType.TEXT
        assert result.data == 'Hello world'
    
    def test_convert_strands_event_tool_use(self):
        """Test converting Strands tool use event."""
        mock_event = Mock(
            type='tool_use',
            tool_name='test_tool',
            arguments={'arg1': 'value1'},
            result='tool result'
        )
        
        result = asyncio.run(self.session_manager._convert_strands_event(mock_event))
        
        assert result.event_type == StreamEventType.TOOL_USE
        assert result.data['tool_name'] == 'test_tool'
        assert result.data['arguments'] == {'arg1': 'value1'}
        assert result.data['result'] == 'tool result'
    
    def test_convert_strands_event_error(self):
        """Test converting Strands error event."""
        mock_event = Mock(type='error', message='Something went wrong')
        
        result = asyncio.run(self.session_manager._convert_strands_event(mock_event))
        
        assert result.event_type == StreamEventType.ERROR
        assert result.data == 'Something went wrong'
    
    def test_convert_strands_event_fallback(self):
        """Test converting unknown Strands event."""
        mock_event = Mock()
        mock_event.__str__ = Mock(return_value='unknown event')
        
        result = asyncio.run(self.session_manager._convert_strands_event(mock_event))
        
        assert result.event_type == StreamEventType.TEXT
        assert result.data == 'unknown event'
    
    @pytest.mark.asyncio
    async def test_end_session_success(self):
        """Test successful session cleanup."""
        # Set up active session
        self.session_manager._session_active = True
        self.session_manager._agent = Mock()
        self.session_manager._tools = [Mock(), Mock()]
        self.session_manager._streaming_handler = Mock()
        
        await self.session_manager.end_session()
        
        # Verify cleanup
        assert not self.session_manager._session_active
        assert self.session_manager._agent is None
        assert len(self.session_manager._tools) == 0
        assert self.session_manager._streaming_handler is None
    
    @pytest.mark.asyncio
    async def test_end_session_not_active(self):
        """Test ending session when not active."""
        # Should not raise an error
        await self.session_manager.end_session()
        assert not self.session_manager._session_active
    
    @pytest.mark.asyncio
    async def test_end_session_with_error(self):
        """Test session cleanup when errors occur."""
        self.session_manager._session_active = True
        mock_agent = Mock()
        mock_agent.cleanup = Mock(side_effect=Exception("Cleanup error"))
        self.session_manager._agent = mock_agent
        
        # Should not raise an error, but force cleanup
        await self.session_manager.end_session()
        
        assert not self.session_manager._session_active
        assert self.session_manager._agent is None
    
    def test_is_active(self):
        """Test session active status check."""
        assert not self.session_manager.is_active()
        
        self.session_manager._session_active = True
        assert self.session_manager.is_active()
    
    def test_get_session_info(self):
        """Test getting session information."""
        # Mock MCP client status
        mock_status = Mock()
        mock_status.model_dump.return_value = {'connected': True}
        self.mcp_client.is_connected.return_value = True
        self.mcp_client.get_connection_status.return_value = mock_status
        
        # Set up session state
        self.session_manager._session_active = True
        self.session_manager._tools = [Mock(), Mock(), Mock()]
        
        info = self.session_manager.get_session_info()
        
        assert info['active'] is True
        assert info['server_name'] == 'test_server'
        assert info['model'] == self.session_config.model
        assert info['tools_loaded'] == 3
        assert info['mcp_connected'] is True
        assert info['connection_status'] == {'connected': True}


class TestStreamingHandler:
    """Test cases for StreamingHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = StreamingHandler()
        self.display_callback_calls = []
        
        def mock_display_callback(event):
            self.display_callback_calls.append(event)
        
        self.mock_display_callback = mock_display_callback
    
    def test_initialization(self):
        """Test StreamingHandler initialization."""
        assert isinstance(self.handler._tool_usage_count, dict)
        assert len(self.handler._tool_usage_count) == 0
        assert isinstance(self.handler._session_start_time, datetime)
        assert self.handler._total_events_processed == 0
        assert self.handler._display_callback is None
        assert self.handler._response_buffer == ""
    
    def test_initialization_with_callback(self):
        """Test StreamingHandler initialization with display callback."""
        handler = StreamingHandler(display_callback=self.mock_display_callback)
        assert handler._display_callback is self.mock_display_callback
    
    def test_handle_stream_event_text(self):
        """Test handling text stream event."""
        event = StreamEvent(event_type=StreamEventType.TEXT, data="Hello world")
        
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
        assert self.handler._response_buffer == "Hello world"
    
    def test_handle_stream_event_multiple_text(self):
        """Test handling multiple text events."""
        events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="Hello "),
            StreamEvent(event_type=StreamEventType.TEXT, data="world"),
            StreamEvent(event_type=StreamEventType.TEXT, data="!"),
        ]
        
        for event in events:
            self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 3
        assert self.handler._response_buffer == "Hello world!"
    
    def test_handle_stream_event_tool_use(self):
        """Test handling tool use stream event."""
        event = StreamEvent(
            event_type=StreamEventType.TOOL_USE,
            data={'tool_name': 'test_tool', 'arguments': {'arg1': 'value1'}, 'result': 'success'}
        )
        
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
        assert self.handler._tool_usage_count['test_tool'] == 1
        
        # Check tool execution tracking
        executions = self.handler.get_current_tool_executions()
        assert len(executions) == 1
        execution = list(executions.values())[0]
        assert execution['tool_name'] == 'test_tool'
        assert execution['arguments'] == {'arg1': 'value1'}
        assert execution['result'] == 'success'
        assert execution['status'] == 'completed'
    
    def test_handle_stream_event_tool_use_without_result(self):
        """Test handling tool use event without result."""
        event = StreamEvent(
            event_type=StreamEventType.TOOL_USE,
            data={'tool_name': 'test_tool', 'arguments': {'arg1': 'value1'}}
        )
        
        self.handler.handle_stream_event(event)
        
        executions = self.handler.get_current_tool_executions()
        execution = list(executions.values())[0]
        assert execution['status'] == 'executing'
        assert execution['result'] is None
    
    def test_handle_stream_event_multiple_tool_uses(self):
        """Test handling multiple tool use events."""
        events = [
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool1', 'arguments': {}}
            ),
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool1', 'arguments': {}}
            ),
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool2', 'arguments': {}}
            ),
        ]
        
        for event in events:
            self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 3
        assert self.handler._tool_usage_count['tool1'] == 2
        assert self.handler._tool_usage_count['tool2'] == 1
        
        # Check tool executions
        executions = self.handler.get_current_tool_executions()
        assert len(executions) == 3
    
    def test_handle_stream_event_error(self):
        """Test handling error stream event."""
        event = StreamEvent(event_type=StreamEventType.ERROR, data="Something went wrong")
        
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
    
    def test_handle_stream_event_status(self):
        """Test handling status stream event."""
        event = StreamEvent(event_type=StreamEventType.STATUS, data="Processing...")
        
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
    
    def test_handle_stream_event_complete(self):
        """Test handling complete stream event."""
        event = StreamEvent(event_type=StreamEventType.COMPLETE, data="Done")
        
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
    
    def test_handle_stream_event_with_callback(self):
        """Test handling events with display callback."""
        self.handler.set_display_callback(self.mock_display_callback)
        
        event = StreamEvent(event_type=StreamEventType.TEXT, data="Hello")
        self.handler.handle_stream_event(event)
        
        assert len(self.display_callback_calls) == 1
        assert self.display_callback_calls[0] == event
    
    def test_handle_stream_event_callback_error(self):
        """Test handling events when callback raises an error."""
        def error_callback(event):
            raise Exception("Callback error")
        
        self.handler.set_display_callback(error_callback)
        
        event = StreamEvent(event_type=StreamEventType.TEXT, data="Hello")
        # Should not raise an error
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
    
    def test_handle_stream_event_invalid_tool_data(self):
        """Test handling tool use event with invalid data."""
        event = StreamEvent(
            event_type=StreamEventType.TOOL_USE,
            data="invalid tool data"
        )
        
        # Should not raise an error
        self.handler.handle_stream_event(event)
        
        assert self.handler._total_events_processed == 1
        assert len(self.handler._tool_usage_count) == 0
    
    def test_get_response_buffer(self):
        """Test getting response buffer."""
        events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="Hello "),
            StreamEvent(event_type=StreamEventType.TEXT, data="world"),
        ]
        
        for event in events:
            self.handler.handle_stream_event(event)
        
        assert self.handler.get_response_buffer() == "Hello world"
    
    def test_clear_response_buffer(self):
        """Test clearing response buffer."""
        event = StreamEvent(event_type=StreamEventType.TEXT, data="Hello world")
        self.handler.handle_stream_event(event)
        
        assert self.handler.get_response_buffer() == "Hello world"
        
        self.handler.clear_response_buffer()
        assert self.handler.get_response_buffer() == ""
    
    def test_get_current_tool_executions(self):
        """Test getting current tool executions."""
        event = StreamEvent(
            event_type=StreamEventType.TOOL_USE,
            data={'tool_name': 'test_tool', 'arguments': {'arg1': 'value1'}}
        )
        
        self.handler.handle_stream_event(event)
        
        executions = self.handler.get_current_tool_executions()
        assert len(executions) == 1
        execution = list(executions.values())[0]
        assert execution['tool_name'] == 'test_tool'
        assert execution['arguments'] == {'arg1': 'value1'}
    
    def test_get_tool_usage_summary(self):
        """Test getting tool usage summary."""
        events = [
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool1', 'arguments': {}}
            ),
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool1', 'arguments': {}}
            ),
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool2', 'arguments': {}}
            ),
        ]
        
        for event in events:
            self.handler.handle_stream_event(event)
        
        summary = self.handler.get_tool_usage_summary()
        
        assert summary['total_tool_calls'] == 3
        assert summary['unique_tools_used'] == 2
        assert summary['most_used_tool']['name'] == 'tool1'
        assert summary['most_used_tool']['count'] == 2
        assert len(summary['recent_executions']) == 3
    
    def test_get_tool_usage_summary_empty(self):
        """Test getting tool usage summary when no tools used."""
        summary = self.handler.get_tool_usage_summary()
        
        assert summary['total_tool_calls'] == 0
        assert summary['unique_tools_used'] == 0
        assert summary['most_used_tool'] is None
        assert len(summary['recent_executions']) == 0
    
    def test_get_usage_stats(self):
        """Test getting comprehensive usage statistics."""
        # Process some events
        events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="Hello world"),
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'tool1', 'arguments': {}}
            ),
            StreamEvent(event_type=StreamEventType.ERROR, data="error"),
        ]
        
        for event in events:
            self.handler.handle_stream_event(event)
        
        stats = self.handler.get_usage_stats()
        
        assert stats['total_events_processed'] == 3
        assert stats['tool_usage_count']['tool1'] == 1
        assert stats['unique_tools_used'] == 1
        assert stats['response_length'] == len("Hello world")
        assert stats['tool_executions'] == 1
        assert 'session_duration' in stats
        assert isinstance(stats['session_duration'], float)
    
    def test_reset_stats(self):
        """Test resetting usage statistics."""
        # Process some events first
        events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="Hello"),
            StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={'tool_name': 'test_tool', 'arguments': {}}
            ),
        ]
        
        for event in events:
            self.handler.handle_stream_event(event)
        
        # Verify stats exist
        assert self.handler._total_events_processed == 2
        assert len(self.handler._tool_usage_count) == 1
        assert self.handler._response_buffer == "Hello"
        assert len(self.handler._current_tool_executions) == 1
        
        # Reset stats
        old_start_time = self.handler._session_start_time
        self.handler.reset_stats()
        
        # Verify reset
        assert self.handler._total_events_processed == 0
        assert len(self.handler._tool_usage_count) == 0
        assert self.handler._response_buffer == ""
        assert len(self.handler._current_tool_executions) == 0
        assert self.handler._session_start_time > old_start_time
    
    def test_set_display_callback(self):
        """Test setting display callback."""
        assert self.handler._display_callback is None
        
        self.handler.set_display_callback(self.mock_display_callback)
        assert self.handler._display_callback is self.mock_display_callback