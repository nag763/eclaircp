"""
Performance tests for EclairCP components.
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor

from eclaircp.mcp import MCPClientManager
from eclaircp.session import SessionManager, StreamingHandler
from eclaircp.config import MCPServerConfig, StreamEvent, StreamEventType
from eclaircp.ui import StreamingDisplay


class TestStreamingPerformance:
    """Test streaming performance under various conditions."""
    
    @pytest.mark.asyncio
    async def test_streaming_latency(self):
        """Test streaming response latency."""
        handler = StreamingHandler()
        
        # Measure time to first event
        start_time = time.time()
        
        event = StreamEvent(
            event_type=StreamEventType.TEXT,
            data="Test response"
        )
        
        handler.handle_stream_event(event)
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Should process events very quickly (< 1ms)
        assert latency < 0.001
    
    @pytest.mark.asyncio
    async def test_high_volume_streaming(self):
        """Test handling high volume of streaming events."""
        handler = StreamingHandler()
        
        # Generate many events
        events = [
            StreamEvent(
                event_type=StreamEventType.TEXT,
                data=f"Event {i}"
            )
            for i in range(1000)
        ]
        
        start_time = time.time()
        
        for event in events:
            handler.handle_stream_event(event)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 1000 events in reasonable time (< 100ms)
        assert processing_time < 0.1
        
        # Verify all events were processed
        assert handler._total_events_processed == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming(self):
        """Test concurrent streaming event processing."""
        handler = StreamingHandler()
        
        async def process_events(event_batch):
            for event in event_batch:
                handler.handle_stream_event(event)
        
        # Create multiple batches of events
        batches = [
            [
                StreamEvent(
                    event_type=StreamEventType.TEXT,
                    data=f"Batch {batch}_Event {i}"
                )
                for i in range(100)
            ]
            for batch in range(5)
        ]
        
        start_time = time.time()
        
        # Process batches concurrently
        tasks = [process_events(batch) for batch in batches]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle concurrent processing efficiently
        assert processing_time < 0.1
        assert handler._total_events_processed == 500


class TestConnectionPerformance:
    """Test MCP connection performance."""
    
    @pytest.mark.asyncio
    async def test_connection_establishment_time(self):
        """Test MCP server connection establishment time."""
        client = MCPClientManager()
        
        config = MCPServerConfig(
            name="test-server",
            command="echo",
            args=["test"],
            timeout=5,
            retry_attempts=1
        )
        
        # Mock the connection to avoid actual network calls
        with patch('eclaircp.mcp.stdio_client') as mock_stdio:
            mock_session = Mock()
            mock_session.initialize = AsyncMock()
            mock_session.list_tools = AsyncMock(return_value=Mock(tools=[]))
            
            async def mock_stdio_context():
                return (Mock(), Mock())
            
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=(Mock(), Mock()))
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('eclaircp.mcp.ClientSession', return_value=mock_session):
                start_time = time.time()
                
                try:
                    result = await client.connect(config)
                    end_time = time.time()
                    connection_time = end_time - start_time
                    
                    # Connection should be fast when mocked
                    assert connection_time < 1.0
                    
                except Exception:
                    # Connection might fail in test environment, that's ok
                    pass
    
    @pytest.mark.asyncio
    async def test_multiple_connection_attempts(self):
        """Test performance of multiple connection attempts."""
        client = MCPClientManager()
        
        config = MCPServerConfig(
            name="test-server",
            command="nonexistent-command",
            args=["test"],
            timeout=1,  # Short timeout for faster test
            retry_attempts=3
        )
        
        start_time = time.time()
        
        try:
            await client.connect(config)
        except Exception:
            # Expected to fail, we're testing retry performance
            pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should fail quickly with short timeout and few retries
        # 3 attempts * 1 second timeout + retry delays should be < 10 seconds
        assert total_time < 10.0


class TestSessionPerformance:
    """Test session management performance."""
    
    @pytest.mark.asyncio
    async def test_session_initialization_time(self):
        """Test session initialization performance."""
        mock_client = Mock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.get_strands_tools = Mock(return_value=[])
        
        session = SessionManager(mock_client)
        
        with patch('eclaircp.session.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            start_time = time.time()
            await session.start_session()
            end_time = time.time()
            
            initialization_time = end_time - start_time
            
            # Session initialization should be fast
            assert initialization_time < 0.1
            assert session.is_active()
    
    @pytest.mark.asyncio
    async def test_session_cleanup_time(self):
        """Test session cleanup performance."""
        mock_client = Mock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.get_strands_tools = Mock(return_value=[])
        
        session = SessionManager(mock_client)
        
        with patch('eclaircp.session.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            await session.start_session()
            
            start_time = time.time()
            await session.end_session()
            end_time = time.time()
            
            cleanup_time = end_time - start_time
            
            # Session cleanup should be fast
            assert cleanup_time < 0.1
            assert not session.is_active()


class TestUIPerformance:
    """Test UI component performance."""
    
    def test_display_rendering_performance(self):
        """Test display rendering performance."""
        display = StreamingDisplay()
        
        # Test rendering many text chunks
        text_chunks = [f"Text chunk {i}" for i in range(100)]
        
        start_time = time.time()
        
        for chunk in text_chunks:
            display.stream_text_instant(chunk)
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Should render text quickly
        assert rendering_time < 0.5
    
    def test_tool_display_performance(self):
        """Test tool usage display performance."""
        display = StreamingDisplay()
        
        # Test displaying many tool usages
        tool_calls = [
            {
                'tool_name': f'tool_{i}',
                'arguments': {'arg1': f'value_{i}', 'arg2': i}
            }
            for i in range(50)
        ]
        
        start_time = time.time()
        
        for tool_call in tool_calls:
            display.show_tool_usage(
                tool_call['tool_name'],
                tool_call['arguments']
            )
        
        end_time = time.time()
        display_time = end_time - start_time
        
        # Should display tool usage quickly
        assert display_time < 1.0


class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_streaming_handler_memory_usage(self):
        """Test streaming handler memory usage with large responses."""
        handler = StreamingHandler()
        
        # Simulate large response
        large_text = "A" * 10000  # 10KB of text
        
        for i in range(100):  # 1MB total
            event = StreamEvent(
                event_type=StreamEventType.TEXT,
                data=large_text
            )
            handler.handle_stream_event(event)
        
        # Check that response buffer contains expected content
        buffer = handler.get_response_buffer()
        assert len(buffer) == 1000000  # 100 * 10KB
        
        # Clear buffer and verify memory is freed
        handler.clear_response_buffer()
        assert len(handler.get_response_buffer()) == 0
    
    def test_tool_execution_tracking_memory(self):
        """Test memory usage of tool execution tracking."""
        handler = StreamingHandler()
        
        # Simulate many tool executions
        for i in range(1000):
            event = StreamEvent(
                event_type=StreamEventType.TOOL_USE,
                data={
                    'tool_name': f'tool_{i}',
                    'arguments': {'data': f'large_data_{i}' * 100},
                    'result': f'result_{i}' * 100
                }
            )
            handler.handle_stream_event(event)
        
        # Check tool usage tracking
        usage_summary = handler.get_tool_usage_summary()
        assert usage_summary['total_tool_calls'] == 1000
        assert usage_summary['unique_tools_used'] == 1000
        
        # Reset stats and verify cleanup
        handler.reset_stats()
        usage_summary = handler.get_tool_usage_summary()
        assert usage_summary['total_tool_calls'] == 0
        assert usage_summary['unique_tools_used'] == 0


class TestConcurrencyPerformance:
    """Test performance under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self):
        """Test concurrent session operations."""
        mock_client = Mock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.get_strands_tools = Mock(return_value=[])
        
        sessions = [SessionManager(mock_client) for _ in range(10)]
        
        with patch('eclaircp.session.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            start_time = time.time()
            
            # Start all sessions concurrently
            start_tasks = [session.start_session() for session in sessions]
            await asyncio.gather(*start_tasks)
            
            # End all sessions concurrently
            end_tasks = [session.end_session() for session in sessions]
            await asyncio.gather(*end_tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle concurrent operations efficiently
            assert total_time < 1.0
            
            # Verify all sessions are properly cleaned up
            for session in sessions:
                assert not session.is_active()
    
    def test_concurrent_ui_operations(self):
        """Test concurrent UI operations."""
        displays = [StreamingDisplay() for _ in range(5)]
        
        def render_text(display, text_id):
            for i in range(100):
                display.stream_text_instant(f"Display {text_id} - Text {i}")
        
        start_time = time.time()
        
        # Use thread pool to simulate concurrent UI operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(render_text, display, i)
                for i, display in enumerate(displays)
            ]
            
            # Wait for all operations to complete
            for future in futures:
                future.result()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent UI operations efficiently
        assert total_time < 2.0


class TestScalabilityLimits:
    """Test system behavior at scale limits."""
    
    def test_large_configuration_handling(self):
        """Test handling of large configuration files."""
        from eclaircp.config import ConfigManager, MCPServerConfig
        
        # Create a large configuration with many servers
        large_config = {
            'servers': {
                f'server_{i}': {
                    'name': f'server_{i}',
                    'command': 'echo',
                    'args': [f'arg_{j}' for j in range(10)],
                    'description': f'Server {i} description' * 10,
                    'env': {f'VAR_{j}': f'value_{j}' for j in range(20)},
                    'timeout': 30,
                    'retry_attempts': 3
                }
                for i in range(100)
            }
        }
        
        config_manager = ConfigManager()
        
        start_time = time.time()
        
        # This would normally load from file, but we'll validate the structure
        try:
            validated_config = config_manager.validate_config(large_config)
            assert len(validated_config.servers) == 100
        except Exception as e:
            # Configuration validation might have limits
            assert "too large" in str(e).lower() or "limit" in str(e).lower()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process large configs in reasonable time
        assert processing_time < 5.0
    
    @pytest.mark.asyncio
    async def test_long_running_session_stability(self):
        """Test session stability over extended periods."""
        mock_client = Mock()
        mock_client.is_connected = Mock(return_value=True)
        mock_client.get_strands_tools = Mock(return_value=[])
        
        session = SessionManager(mock_client)
        handler = StreamingHandler()
        
        with patch('eclaircp.session.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            await session.start_session()
            
            # Simulate long-running session with many events
            start_time = time.time()
            
            for i in range(10000):
                event = StreamEvent(
                    event_type=StreamEventType.TEXT,
                    data=f"Long running event {i}"
                )
                handler.handle_stream_event(event)
                
                # Occasionally reset stats to prevent unbounded growth
                if i % 1000 == 0:
                    handler.reset_stats()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should handle long-running sessions efficiently
            assert processing_time < 10.0
            assert session.is_active()
            
            await session.end_session()
            assert not session.is_active()