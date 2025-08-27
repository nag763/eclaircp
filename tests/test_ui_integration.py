"""
Integration tests for UI components.
"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
from rich.console import Console

from eclaircp.ui import StreamingDisplay, ServerSelector, StatusDisplay
from eclaircp.config import MCPServerConfig, ToolInfo


class TestUIIntegration:
    """Integration tests for UI components working together."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use StringIO to capture console output
        self.output = StringIO()
        self.console = Console(file=self.output, width=80)

        # Create UI components
        self.streaming_display = StreamingDisplay(console=self.console)
        self.server_selector = ServerSelector(console=self.console)
        self.status_display = StatusDisplay(console=self.console)

        # Create sample data
        self.servers = {
            "aws-docs": MCPServerConfig(
                name="aws-docs",
                command="uvx",
                args=["awslabs.aws-documentation-mcp-server@latest"],
                description="AWS Documentation MCP Server",
            ),
            "github": MCPServerConfig(
                name="github",
                command="uvx",
                args=["github-mcp-server"],
                description="GitHub MCP Server",
            ),
        }

        self.tools = [
            ToolInfo(
                name="search_docs",
                description="Search AWS documentation",
                parameters={"query": "string", "service": "string"},
            ),
            ToolInfo(
                name="get_service_info",
                description="Get information about AWS service",
                parameters={"service_name": "string"},
            ),
        ]

    def test_complete_server_selection_flow(self):
        """Test complete server selection and status display flow."""
        # Test single server selection (should auto-select)
        single_server = {"aws-docs": self.servers["aws-docs"]}
        selected = self.server_selector.select_server(single_server)

        assert selected == "aws-docs"

        # Check that output was generated
        output = self.output.getvalue()
        assert "aws-docs" in output
        assert "✅" in output  # Success indicator

    def test_server_info_and_connection_status_flow(self):
        """Test displaying server info followed by connection status."""
        server_config = self.servers["aws-docs"]

        # Show server info
        self.status_display.show_server_info(server_config, connection_status=None)

        # Show connection attempt
        self.status_display.show_operation_status(
            "Connecting", "in_progress", "Establishing connection..."
        )

        # Show successful connection
        self.status_display.show_connection_status(
            "aws-docs",
            True,
            connection_time="2024-01-01 12:00:00",
            available_tools=["search_docs", "get_service_info"],
        )

        # Show available tools
        self.status_display.show_tools_list(self.tools)

        # Check output contains expected elements
        output = self.output.getvalue()
        assert "aws-docs" in output
        assert "Connecting" in output
        assert "Connected" in output
        assert "search_docs" in output
        assert "get_service_info" in output

    def test_error_handling_flow(self):
        """Test error handling and display flow."""
        # Show connection failure
        error_msg = "Connection timeout after 30 seconds"
        suggestions = [
            "Check your internet connection",
            "Verify the server is running",
            "Check firewall settings",
        ]

        self.status_display.show_connection_status(
            "aws-docs", False, error_message=error_msg
        )
        self.status_display.show_error_with_suggestions(error_msg, suggestions)

        # Check output contains error information
        output = self.output.getvalue()
        assert "Failed to connect" in output
        assert error_msg in output
        assert "Check your internet connection" in output

    def test_streaming_and_tool_usage_flow(self):
        """Test streaming display with tool usage."""
        # Stream some text
        self.streaming_display.stream_text_instant("Processing your request...")

        # Show tool usage
        self.streaming_display.show_tool_usage(
            "search_docs", {"query": "EC2 instances", "service": "ec2"}
        )

        # Show tool result
        result = {
            "results": [
                {
                    "title": "EC2 Instance Types",
                    "url": "https://docs.aws.amazon.com/ec2/...",
                },
                {
                    "title": "Launching EC2 Instances",
                    "url": "https://docs.aws.amazon.com/ec2/...",
                },
            ],
            "count": 2,
        }
        self.streaming_display.show_tool_result("search_docs", result)

        # Stream response
        self.streaming_display.stream_text_instant(
            "\nBased on the search results, here are the key EC2 documentation pages..."
        )

        # Check output contains expected elements
        output = self.output.getvalue()
        assert "Processing your request" in output
        assert "search_docs" in output
        assert "EC2 instances" in output
        assert "results" in output
        assert "Based on the search results" in output

    def test_status_messages_flow(self):
        """Test various status message types."""
        # Show different status types
        self.status_display.show_operation_status(
            "Initializing", "info", "Starting up..."
        )
        self.status_display.show_operation_status(
            "Connected", "success", "Connection established"
        )
        self.status_display.show_operation_status(
            "Warning", "warning", "High memory usage detected"
        )
        self.status_display.show_operation_status("Failed", "error", "Operation failed")

        # Check output contains all status types
        output = self.output.getvalue()
        assert "Initializing" in output
        assert "Connected" in output
        assert "Warning" in output
        assert "Failed" in output

        # Check for status indicators
        assert "ℹ️" in output or "info" in output.lower()
        assert "✅" in output or "success" in output.lower()
        assert "⚠️" in output or "warning" in output.lower()
        assert "❌" in output or "error" in output.lower()

    @patch("time.sleep")  # Mock sleep to speed up test
    def test_streaming_text_with_formatting(self, mock_sleep):
        """Test streaming text with various formatting."""
        # Test plain text
        self.streaming_display.stream_text("Hello, this is plain text.\n")

        # Test with code block
        code_text = "Here's some Python code:\n```python\nprint('Hello, World!')\n```\n"
        self.streaming_display.stream_text_instant(code_text)

        # Test error display
        self.streaming_display.show_error("Something went wrong", "Validation Error")

        # Check output
        output = self.output.getvalue()
        assert "Hello, this is plain text" in output
        assert "print('Hello, World!')" in output  # Check for the actual code content
        assert "Something went wrong" in output

    def get_output(self) -> str:
        """Get the current console output."""
        return self.output.getvalue()

    def clear_output(self):
        """Clear the console output buffer."""
        self.output.seek(0)
        self.output.truncate(0)
