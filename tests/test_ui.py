"""
Tests for the UI components module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from rich.console import Console
from rich.progress import Progress

from eclaircp.ui import StreamingDisplay, ServerSelector, StatusDisplay
from eclaircp.config import MCPServerConfig, ToolInfo


class TestStreamingDisplay:
    """Test cases for StreamingDisplay class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock console to capture output
        self.mock_console = Mock(spec=Console)
        self.mock_console.file = Mock()
        self.mock_console.file.flush = Mock()
        self.display = StreamingDisplay(console=self.mock_console)

    def test_initialization_with_console(self):
        """Test StreamingDisplay initialization with provided console."""
        display = StreamingDisplay(console=self.mock_console)
        assert display.console == self.mock_console
        assert display._current_text == ""
        assert display._live_display is None

    def test_initialization_without_console(self):
        """Test StreamingDisplay initialization without console creates new one."""
        display = StreamingDisplay()
        assert display.console is not None
        assert isinstance(display.console, Console)

    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_stream_text(self, mock_sleep):
        """Test streaming text display."""
        test_text = "Hello World"
        self.display.stream_text(test_text)

        # Verify text was added to buffer
        assert self.display._current_text == test_text

        # Verify console.print was called for each character
        assert self.mock_console.print.call_count == len(test_text)

        # Verify flush was called
        self.mock_console.file.flush.assert_called_once()

    def test_stream_text_instant(self):
        """Test instant text display without streaming effect."""
        test_text = "Instant text"
        self.display.stream_text_instant(test_text)

        # Verify text was added to buffer
        assert self.display._current_text == test_text

        # Verify console.print was called once
        self.mock_console.print.assert_called_once()

    def test_show_tool_usage(self):
        """Test tool usage display."""
        tool_name = "test_tool"
        args = {"param1": "value1", "param2": {"nested": "value"}, "param3": [1, 2, 3]}

        self.display.show_tool_usage(tool_name, args)

        # Verify console.print was called with a Panel
        self.mock_console.print.assert_called_once()
        call_args = self.mock_console.print.call_args[0]
        assert len(call_args) == 1
        # The panel should contain the tool name in the title
        panel = call_args[0]
        assert hasattr(panel, "title")

    def test_show_tool_result_dict(self):
        """Test tool result display with dictionary result."""
        tool_name = "test_tool"
        result = {"status": "success", "data": "test"}

        self.display.show_tool_result(tool_name, result)

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_tool_result_string(self):
        """Test tool result display with string result."""
        tool_name = "test_tool"
        result = "Simple string result"

        self.display.show_tool_result(tool_name, result)

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_error(self):
        """Test error message display."""
        error_message = "Something went wrong"
        error_type = "Connection Error"

        self.display.show_error(error_message, error_type)

        # Verify console.print was called with a Panel
        self.mock_console.print.assert_called_once()

    def test_show_error_default_type(self):
        """Test error message display with default error type."""
        error_message = "Something went wrong"

        self.display.show_error(error_message)

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_status_info(self):
        """Test status message display with info type."""
        message = "Processing request"

        self.display.show_status(message, "info")

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_status_success(self):
        """Test status message display with success type."""
        message = "Operation completed"

        self.display.show_status(message, "success")

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_status_warning(self):
        """Test status message display with warning type."""
        message = "Potential issue detected"

        self.display.show_status(message, "warning")

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_status_error(self):
        """Test status message display with error type."""
        message = "Operation failed"

        self.display.show_status(message, "error")

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    def test_show_status_unknown_type(self):
        """Test status message display with unknown type defaults to info."""
        message = "Unknown status"

        self.display.show_status(message, "unknown_type")

        # Verify console.print was called
        self.mock_console.print.assert_called_once()

    @patch("eclaircp.ui.Progress")
    def test_show_loading(self, mock_progress_class):
        """Test loading indicator display."""
        mock_progress = Mock(spec=Progress)
        mock_progress_class.return_value = mock_progress

        message = "Loading data..."
        result = self.display.show_loading(message)

        # Verify Progress was created and started
        mock_progress_class.assert_called_once()
        mock_progress.add_task.assert_called_once()
        mock_progress.start.assert_called_once()
        assert result == mock_progress

    def test_clear_current_text(self):
        """Test clearing current text buffer."""
        self.display._current_text = "Some text"
        self.display.clear_current_text()
        assert self.display._current_text == ""

    def test_format_streaming_text_plain(self):
        """Test formatting plain text."""
        text = "Plain text without special formatting"
        result = self.display._format_streaming_text(text)

        # Should return a Text object
        assert hasattr(result, "plain")  # Rich Text objects have a plain property

    def test_format_streaming_text_with_code_blocks(self):
        """Test formatting text with code blocks."""
        text = "Here's some code:\n```python\nprint('hello')\n```"
        result = self.display._format_streaming_text(text)

        # Should handle code blocks
        assert result is not None

    def test_format_code_blocks_python(self):
        """Test formatting Python code blocks."""
        text = "```python\ndef hello():\n    print('world')\n```"
        result = self.display._format_code_blocks(text)

        # Should return formatted syntax
        assert result is not None

    def test_format_code_blocks_no_language(self):
        """Test formatting code blocks without language specification."""
        text = "No code blocks here"
        result = self.display._format_code_blocks(text)

        # Should return Text object
        assert hasattr(result, "plain")

    def test_create_tool_usage_content(self):
        """Test creating tool usage content table."""
        tool_name = "test_tool"
        args = {
            "string_param": "value",
            "dict_param": {"key": "value"},
            "list_param": [1, 2, 3],
        }

        result = self.display._create_tool_usage_content(tool_name, args)

        # Should return a Table
        assert hasattr(result, "add_row")  # Tables have add_row method

    def test_format_result_content_json(self):
        """Test formatting JSON result content."""
        result = '{"key": "value", "number": 42}'
        formatted = self.display._format_result_content(result)

        # Should detect and format as JSON
        assert formatted is not None

    def test_format_result_content_python_code(self):
        """Test formatting Python code result content."""
        result = "def hello():\n    print('world')\n    return True"
        formatted = self.display._format_result_content(result)

        # Should detect and format as Python code
        assert formatted is not None

    def test_format_result_content_javascript_code(self):
        """Test formatting JavaScript code result content."""
        result = "function hello() {\n    console.log('world');\n    return true;\n}"
        formatted = self.display._format_result_content(result)

        # Should detect and format as JavaScript code
        assert formatted is not None

    def test_format_result_content_markdown(self):
        """Test formatting Markdown result content."""
        result = "# Title\n\n* Item 1\n* Item 2\n\n```code```"
        formatted = self.display._format_result_content(result)

        # Should detect and format as Markdown
        assert formatted is not None

    def test_format_result_content_plain_text(self):
        """Test formatting plain text result content."""
        result = "Just plain text without special formatting"
        formatted = self.display._format_result_content(result)

        # Should return Text object
        assert hasattr(formatted, "plain")


class TestServerSelector:
    """Test cases for ServerSelector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)
        self.selector = ServerSelector(console=self.mock_console)

        # Create sample server configs
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

    def test_initialization_with_console(self):
        """Test ServerSelector initialization with provided console."""
        selector = ServerSelector(console=self.mock_console)
        assert selector.console == self.mock_console
        assert selector._selected_server is None

    def test_initialization_without_console(self):
        """Test ServerSelector initialization without console creates new one."""
        selector = ServerSelector()
        assert selector.console is not None
        assert isinstance(selector.console, Console)

    def test_select_server_empty_servers(self):
        """Test select_server with empty servers dict raises ValueError."""
        with pytest.raises(ValueError, match="No servers available"):
            self.selector.select_server({})

    def test_select_server_single_server(self):
        """Test select_server with single server returns it directly."""
        single_server = {"test": self.servers["aws-docs"]}
        result = self.selector.select_server(single_server)

        assert result == "test"
        self.mock_console.print.assert_called()

    @patch("builtins.input", return_value="1")
    def test_select_server_numeric_choice(self, mock_input):
        """Test select_server with numeric choice."""
        self.mock_console.input.return_value = "1"

        result = self.selector.select_server(self.servers)

        assert result in self.servers
        self.mock_console.print.assert_called()

    @patch("builtins.input", return_value="aws-docs")
    def test_select_server_name_choice(self, mock_input):
        """Test select_server with exact name choice."""
        self.mock_console.input.return_value = "aws-docs"

        result = self.selector.select_server(self.servers)

        assert result == "aws-docs"
        self.mock_console.print.assert_called()

    @patch("builtins.input", return_value="aws")
    def test_select_server_partial_match(self, mock_input):
        """Test select_server with partial name match."""
        self.mock_console.input.return_value = "aws"

        result = self.selector.select_server(self.servers)

        assert result == "aws-docs"
        self.mock_console.print.assert_called()

    @patch("builtins.input", return_value="quit")
    def test_select_server_quit(self, mock_input):
        """Test select_server with quit command raises ValueError."""
        self.mock_console.input.return_value = "quit"

        with pytest.raises(ValueError, match="cancelled by user"):
            self.selector.select_server(self.servers)

    @patch("builtins.input", side_effect=["invalid", "1"])
    def test_select_server_invalid_then_valid(self, mock_input):
        """Test select_server with invalid input then valid input."""
        self.mock_console.input.side_effect = ["invalid", "1"]

        result = self.selector.select_server(self.servers)

        assert result in self.servers
        # Should have printed error message for invalid input
        assert self.mock_console.print.call_count >= 2

    def test_display_server_menu(self):
        """Test _display_server_menu creates and prints table."""
        self.selector._display_server_menu(self.servers)

        # Should print table and instructions
        assert self.mock_console.print.call_count == 2


class TestStatusDisplay:
    """Test cases for StatusDisplay class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_console = Mock(spec=Console)
        self.status_display = StatusDisplay(console=self.mock_console)

        # Create sample server config
        self.server_config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test-server"],
            description="Test MCP Server",
        )

        # Create sample tool info
        self.tools = [
            ToolInfo(
                name="test_tool",
                description="A test tool",
                parameters={"param1": "string", "param2": "number"},
            ),
            ToolInfo(
                name="another_tool", description="Another test tool", parameters={}
            ),
        ]

    def test_initialization_with_console(self):
        """Test StatusDisplay initialization with provided console."""
        status = StatusDisplay(console=self.mock_console)
        assert status.console == self.mock_console

    def test_initialization_without_console(self):
        """Test StatusDisplay initialization without console creates new one."""
        status = StatusDisplay()
        assert status.console is not None
        assert isinstance(status.console, Console)

    def test_show_connection_status_connected(self):
        """Test show_connection_status with successful connection."""
        self.status_display.show_connection_status(
            "test-server",
            True,
            connection_time="2024-01-01 12:00:00",
            available_tools=["tool1", "tool2"],
        )

        # Should print connection success message
        self.mock_console.print.assert_called()
        assert self.mock_console.print.call_count >= 1

    def test_show_connection_status_disconnected(self):
        """Test show_connection_status with failed connection."""
        error_msg = "Connection timeout"
        self.status_display.show_connection_status(
            "test-server", False, error_message=error_msg
        )

        # Should print error message
        self.mock_console.print.assert_called()
        assert self.mock_console.print.call_count >= 1

    def test_show_server_info(self):
        """Test show_server_info displays server configuration."""
        self.status_display.show_server_info(self.server_config, connection_status=True)

        # Should print server info panel
        self.mock_console.print.assert_called_once()

    def test_show_server_info_no_connection_status(self):
        """Test show_server_info without connection status."""
        self.status_display.show_server_info(self.server_config)

        # Should print server info panel
        self.mock_console.print.assert_called_once()

    def test_show_operation_status_success(self):
        """Test show_operation_status with success status."""
        self.status_display.show_operation_status(
            "Connect", "success", "Connected successfully"
        )

        self.mock_console.print.assert_called_once()

    def test_show_operation_status_error(self):
        """Test show_operation_status with error status."""
        self.status_display.show_operation_status(
            "Connect", "error", "Connection failed"
        )

        self.mock_console.print.assert_called_once()

    def test_show_operation_status_unknown_status(self):
        """Test show_operation_status with unknown status defaults to info."""
        self.status_display.show_operation_status(
            "Connect", "unknown", "Unknown status"
        )

        self.mock_console.print.assert_called_once()

    def test_show_tools_list_with_tools(self):
        """Test show_tools_list with available tools."""
        self.status_display.show_tools_list(self.tools)

        # Should print tools table
        self.mock_console.print.assert_called_once()

    def test_show_tools_list_empty(self):
        """Test show_tools_list with no tools."""
        self.status_display.show_tools_list([])

        # Should print "no tools" message
        self.mock_console.print.assert_called_once()

    def test_show_error_with_suggestions(self):
        """Test show_error_with_suggestions displays error and suggestions."""
        error_msg = "Connection failed"
        suggestions = ["Check network connection", "Verify server configuration"]

        self.status_display.show_error_with_suggestions(error_msg, suggestions)

        # Should print error panel and suggestions panel
        assert self.mock_console.print.call_count == 2

    def test_show_error_with_no_suggestions(self):
        """Test show_error_with_suggestions with empty suggestions."""
        error_msg = "Connection failed"

        self.status_display.show_error_with_suggestions(error_msg, [])

        # Should print only error panel
        self.mock_console.print.assert_called_once()

    def test_show_connected_status_with_tools(self):
        """Test _show_connected_status with tools list."""
        self.status_display._show_connected_status(
            "test-server",
            connection_time="2024-01-01 12:00:00",
            available_tools=["tool1", "tool2", "tool3"],
        )

        # Should print connection status and tools info
        assert self.mock_console.print.call_count >= 2

    def test_show_connected_status_many_tools(self):
        """Test _show_connected_status with many tools (truncation)."""
        many_tools = [f"tool{i}" for i in range(10)]

        self.status_display._show_connected_status(
            "test-server", available_tools=many_tools
        )

        # Should print connection status and truncated tools info
        assert self.mock_console.print.call_count >= 2

    def test_show_disconnected_status_with_error(self):
        """Test _show_disconnected_status with error message."""
        error_msg = "Connection timeout after 30 seconds"

        self.status_display._show_disconnected_status("test-server", error_msg)

        # Should print disconnection status and error panel
        assert self.mock_console.print.call_count == 2

    def test_show_disconnected_status_no_error(self):
        """Test _show_disconnected_status without error message."""
        self.status_display._show_disconnected_status("test-server")

        # Should print only disconnection status
        self.mock_console.print.assert_called_once()
