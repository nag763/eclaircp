"""
EclairCP session management module.
"""

import asyncio
import logging
from typing import Dict, Optional, AsyncGenerator, Any, Callable
from datetime import datetime

from strands import Agent

from .mcp import MCPClientManager
from .config import SessionConfig, StreamEvent, StreamEventType


logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversational sessions using Strands Agents."""
    
    def __init__(self, mcp_client: MCPClientManager, session_config: Optional[SessionConfig] = None):
        """
        Initialize session with MCP client.
        
        Args:
            mcp_client: MCP client manager instance
            session_config: Optional session configuration
        """
        self.mcp_client = mcp_client
        self.session_config = session_config or SessionConfig(server_name="default")
        self._session_active = False
        self._agent: Optional[Agent] = None
        self._tools: list = []
        self._streaming_handler: Optional['StreamingHandler'] = None
    
    async def start_session(self) -> None:
        """Begin interactive session with MCP tools loading."""
        if self._session_active:
            logger.warning("Session is already active")
            return
        
        try:
            # Ensure MCP client is connected
            if not self.mcp_client.is_connected():
                raise RuntimeError("MCP client is not connected. Connect to a server first.")
            
            # Load MCP tools for Strands integration
            logger.info("Loading MCP tools for Strands integration...")
            self._tools = self.mcp_client.get_strands_tools()
            logger.info(f"Loaded {len(self._tools)} MCP tools")
            
            # Initialize Strands agent with MCP tools
            logger.info("Initializing Strands agent...")
            self._agent = Agent(
                model=self.session_config.model,
                system_prompt=self.session_config.system_prompt,
                tools=self._tools,
                max_context_length=self.session_config.max_context_length
            )
            
            # Initialize streaming handler
            self._streaming_handler = StreamingHandler()
            
            self._session_active = True
            logger.info("Session started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            await self.end_session()
            raise RuntimeError(f"Failed to start session: {e}") from e
    
    async def process_input(self, user_input: str) -> AsyncGenerator[StreamEvent, None]:
        """
        Process user input through Strands agent with streaming.
        
        Args:
            user_input: User's input message
            
        Yields:
            StreamEvent objects containing response data
            
        Raises:
            RuntimeError: If session is not active or agent is not initialized
        """
        if not self._session_active or not self._agent:
            raise RuntimeError("Session is not active. Call start_session() first.")
        
        if not user_input.strip():
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data="Empty input provided"
            )
            return
        
        try:
            logger.info(f"Processing user input: {user_input[:100]}...")
            
            # Send status event
            yield StreamEvent(
                event_type=StreamEventType.STATUS,
                data="Processing your request..."
            )
            
            # Process through Strands agent with streaming
            async for event in self._agent.stream_async(user_input):
                # Convert Strands events to our StreamEvent format
                stream_event = await self._convert_strands_event(event)
                if stream_event:
                    yield stream_event
            
            # Send completion event
            yield StreamEvent(
                event_type=StreamEventType.COMPLETE,
                data="Response complete"
            )
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data=f"Error processing input: {str(e)}"
            )
    
    async def _convert_strands_event(self, strands_event: Any) -> Optional[StreamEvent]:
        """
        Convert Strands agent events to StreamEvent format.
        
        Args:
            strands_event: Event from Strands agent
            
        Returns:
            StreamEvent or None if event should be filtered
        """
        try:
            # Handle different types of Strands events
            if hasattr(strands_event, 'type'):
                event_type = strands_event.type
                
                if event_type == 'text':
                    return StreamEvent(
                        event_type=StreamEventType.TEXT,
                        data=strands_event.text if hasattr(strands_event, 'text') else str(strands_event)
                    )
                elif event_type == 'tool_use':
                    return StreamEvent(
                        event_type=StreamEventType.TOOL_USE,
                        data={
                            'tool_name': getattr(strands_event, 'tool_name', 'unknown'),
                            'arguments': getattr(strands_event, 'arguments', {}),
                            'result': getattr(strands_event, 'result', None)
                        }
                    )
                elif event_type == 'error':
                    return StreamEvent(
                        event_type=StreamEventType.ERROR,
                        data=getattr(strands_event, 'message', str(strands_event))
                    )
            
            # Fallback: treat as text event
            return StreamEvent(
                event_type=StreamEventType.TEXT,
                data=str(strands_event)
            )
            
        except Exception as e:
            logger.warning(f"Error converting Strands event: {e}")
            return StreamEvent(
                event_type=StreamEventType.ERROR,
                data=f"Event conversion error: {str(e)}"
            )
    
    async def end_session(self) -> None:
        """Clean up session without persisting context."""
        if not self._session_active:
            logger.info("Session is not active, nothing to clean up")
            return
        
        try:
            logger.info("Ending session...")
            
            # Clean up agent (no persistence needed as per requirements)
            if self._agent:
                # Strands agents don't require explicit cleanup in most cases
                # but we'll clear the reference
                self._agent = None
            
            # Clear tools
            self._tools.clear()
            
            # Clear streaming handler
            self._streaming_handler = None
            
            self._session_active = False
            logger.info("Session ended successfully")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            # Force cleanup even if there are errors
            self._agent = None
            self._tools.clear()
            self._streaming_handler = None
            self._session_active = False
    
    def is_active(self) -> bool:
        """
        Check if session is currently active.
        
        Returns:
            True if session is active, False otherwise
        """
        return self._session_active
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary containing session information
        """
        return {
            'active': self._session_active,
            'server_name': self.session_config.server_name,
            'model': self.session_config.model,
            'tools_loaded': len(self._tools),
            'mcp_connected': self.mcp_client.is_connected(),
            'connection_status': self.mcp_client.get_connection_status().model_dump()
        }


class StreamingHandler:
    """Processes and displays streaming responses from Strands agent."""
    
    def __init__(self, display_callback: Optional[Callable[[StreamEvent], None]] = None):
        """
        Initialize the streaming handler.
        
        Args:
            display_callback: Optional callback function for displaying events
        """
        self._tool_usage_count: Dict[str, int] = {}
        self._session_start_time: datetime = datetime.now()
        self._total_events_processed: int = 0
        self._display_callback = display_callback
        self._current_tool_executions: Dict[str, Dict[str, Any]] = {}
        self._response_buffer: str = ""
    
    def handle_stream_event(self, event: StreamEvent) -> None:
        """
        Process streaming events from Strands agent with real-time display.
        
        Args:
            event: StreamEvent object containing event data
        """
        self._total_events_processed += 1
        
        # Process different event types
        if event.event_type == StreamEventType.TEXT:
            self._handle_text_event(event)
        elif event.event_type == StreamEventType.TOOL_USE:
            self._handle_tool_use_event(event)
        elif event.event_type == StreamEventType.ERROR:
            self._handle_error_event(event)
        elif event.event_type == StreamEventType.STATUS:
            self._handle_status_event(event)
        elif event.event_type == StreamEventType.COMPLETE:
            self._handle_complete_event(event)
        
        # Call display callback if provided
        if self._display_callback:
            try:
                self._display_callback(event)
            except Exception as e:
                logger.warning(f"Display callback error: {e}")
        
        # Log the event for debugging
        logger.debug(f"Processed {event.event_type} event: {event.data}")
    
    def _handle_text_event(self, event: StreamEvent) -> None:
        """
        Handle text streaming events.
        
        Args:
            event: Text event to process
        """
        text_data = str(event.data)
        self._response_buffer += text_data
        
        # For real-time display, we could implement word-by-word or chunk-by-chunk streaming
        # This is a basic implementation that accumulates text
        logger.debug(f"Text event: {text_data}")
    
    def _handle_tool_use_event(self, event: StreamEvent) -> None:
        """
        Handle tool use events with tracking and display.
        
        Args:
            event: Tool use event to process
        """
        tool_data = event.data
        if isinstance(tool_data, dict) and 'tool_name' in tool_data:
            tool_name = tool_data['tool_name']
            
            # Track tool usage
            self._tool_usage_count[tool_name] = self._tool_usage_count.get(tool_name, 0) + 1
            
            # Track current tool execution
            execution_id = f"{tool_name}_{self._tool_usage_count[tool_name]}"
            self._current_tool_executions[execution_id] = {
                'tool_name': tool_name,
                'arguments': tool_data.get('arguments', {}),
                'result': tool_data.get('result'),
                'timestamp': event.timestamp,
                'status': 'completed' if 'result' in tool_data else 'executing'
            }
            
            logger.info(f"Tool '{tool_name}' executed with args: {tool_data.get('arguments', {})}")
    
    def _handle_error_event(self, event: StreamEvent) -> None:
        """
        Handle error events.
        
        Args:
            event: Error event to process
        """
        error_message = str(event.data)
        logger.error(f"Stream error: {error_message}")
        
        # Could implement error recovery or user notification here
    
    def _handle_status_event(self, event: StreamEvent) -> None:
        """
        Handle status events.
        
        Args:
            event: Status event to process
        """
        status_message = str(event.data)
        logger.info(f"Status: {status_message}")
    
    def _handle_complete_event(self, event: StreamEvent) -> None:
        """
        Handle completion events.
        
        Args:
            event: Complete event to process
        """
        logger.info("Stream processing complete")
        
        # Could implement final processing or cleanup here
    
    def get_response_buffer(self) -> str:
        """
        Get the accumulated response text.
        
        Returns:
            Complete response text accumulated from text events
        """
        return self._response_buffer
    
    def clear_response_buffer(self) -> None:
        """Clear the response buffer."""
        self._response_buffer = ""
    
    def get_current_tool_executions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about current/recent tool executions.
        
        Returns:
            Dictionary of tool execution information
        """
        return self._current_tool_executions.copy()
    
    def get_tool_usage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of tool usage during the session.
        
        Returns:
            Dictionary containing tool usage summary
        """
        total_tool_calls = sum(self._tool_usage_count.values())
        most_used_tool = max(self._tool_usage_count.items(), key=lambda x: x[1]) if self._tool_usage_count else None
        
        return {
            'total_tool_calls': total_tool_calls,
            'unique_tools_used': len(self._tool_usage_count),
            'tool_usage_count': self._tool_usage_count.copy(),
            'most_used_tool': {
                'name': most_used_tool[0],
                'count': most_used_tool[1]
            } if most_used_tool else None,
            'recent_executions': list(self._current_tool_executions.values())[-5:]  # Last 5 executions
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about event processing and tool usage.
        
        Returns:
            Dictionary containing usage statistics
        """
        return {
            'session_duration': (datetime.now() - self._session_start_time).total_seconds(),
            'total_events_processed': self._total_events_processed,
            'tool_usage_count': self._tool_usage_count.copy(),
            'unique_tools_used': len(self._tool_usage_count),
            'response_length': len(self._response_buffer),
            'tool_executions': len(self._current_tool_executions)
        }
    
    def reset_stats(self) -> None:
        """Reset usage statistics and clear buffers."""
        self._tool_usage_count.clear()
        self._session_start_time = datetime.now()
        self._total_events_processed = 0
        self._current_tool_executions.clear()
        self._response_buffer = ""
    
    def set_display_callback(self, callback: Callable[[StreamEvent], None]) -> None:
        """
        Set or update the display callback function.
        
        Args:
            callback: Function to call for displaying events
        """
        self._display_callback = callback