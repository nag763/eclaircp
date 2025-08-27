"""
EclairCP user interface components module.
"""

import sys
import time
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.markdown import Markdown
from rich.json import JSON

from .config import MCPServerConfig, StreamEvent, StreamEventType, ToolInfo


class StreamingDisplay:
    """Real-time response rendering with Rich formatting."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the streaming display.

        Args:
            console: Rich console instance, creates new one if None
        """
        self.console = console or Console()
        self._current_text = ""
        self._live_display: Optional[Live] = None

    def stream_text(self, text: str) -> None:
        """
        Display streaming text with formatting.

        Args:
            text: Text to display with streaming effect
        """
        # Add text to current buffer
        self._current_text += text

        # Create formatted text with syntax highlighting for code blocks
        formatted_text = self._format_streaming_text(self._current_text)

        # Print character by character for streaming effect
        for char in text:
            self.console.print(char, end="", style="bright_white")
            time.sleep(0.01)  # Small delay for streaming effect

        # Flush the output
        self.console.file.flush()

    def stream_text_instant(self, text: str) -> None:
        """
        Display text instantly without streaming effect.

        Args:
            text: Text to display immediately
        """
        self._current_text += text
        formatted_text = self._format_streaming_text(text)
        self.console.print(formatted_text, end="")

    def show_tool_usage(self, tool_name: str, args: Dict[str, Any]) -> None:
        """
        Display tool execution information with structured formatting.

        Args:
            tool_name: Name of the tool being used
            args: Tool arguments dictionary
        """
        # Create a panel for tool usage
        tool_panel = Panel(
            self._create_tool_usage_content(tool_name, args),
            title=f"🔧 Tool: {tool_name}",
            title_align="left",
            border_style="blue",
            padding=(0, 1),
        )

        self.console.print(tool_panel)

    def show_tool_result(self, tool_name: str, result: Any) -> None:
        """
        Display tool execution result.

        Args:
            tool_name: Name of the tool that was executed
            result: Result from tool execution
        """
        # Format result based on type
        if isinstance(result, dict):
            result_content = JSON.from_data(result)
        elif isinstance(result, str):
            # Try to detect if it's JSON, code, or plain text
            result_content = self._format_result_content(result)
        else:
            result_content = str(result)

        result_panel = Panel(
            result_content,
            title=f"✅ Result: {tool_name}",
            title_align="left",
            border_style="green",
            padding=(0, 1),
        )

        self.console.print(result_panel)

    def show_error(self, error: str, error_type: str = "Error") -> None:
        """
        Display error messages with clear visual distinction.

        Args:
            error: Error message to display
            error_type: Type of error (e.g., "Connection Error", "Validation Error")
        """
        error_text = Text(error, style="red")
        error_panel = Panel(
            error_text,
            title=f"❌ {error_type}",
            title_align="left",
            border_style="red",
            padding=(0, 1),
        )

        self.console.print(error_panel)

    def show_status(self, message: str, status_type: str = "info") -> None:
        """
        Display status messages with appropriate styling.

        Args:
            message: Status message to display
            status_type: Type of status (info, success, warning, error)
        """
        style_map = {
            "info": ("ℹ️", "blue"),
            "success": ("✅", "green"),
            "warning": ("⚠️", "yellow"),
            "error": ("❌", "red"),
        }

        icon, color = style_map.get(status_type, ("ℹ️", "blue"))

        status_text = Text(message, style=color)
        self.console.print(f"{icon} {status_text}")

    def show_loading(self, message: str = "Processing...") -> Progress:
        """
        Display a loading indicator with spinner.

        Args:
            message: Loading message to display

        Returns:
            Progress: Progress object that can be used to update or stop loading
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )

        progress.add_task(description=message, total=None)
        progress.start()
        return progress

    def clear_current_text(self) -> None:
        """Clear the current text buffer."""
        self._current_text = ""

    def _format_streaming_text(self, text: str) -> Text:
        """
        Format text with syntax highlighting and markdown-like formatting.

        Args:
            text: Raw text to format

        Returns:
            Text: Formatted Rich Text object
        """
        # Simple markdown-like formatting
        formatted = Text(text)

        # Apply basic styling
        if "```" in text:
            # Handle code blocks - this is simplified, real implementation would be more robust
            return self._format_code_blocks(text)

        return formatted

    def _format_code_blocks(self, text: str) -> Text:
        """
        Format code blocks with syntax highlighting.

        Args:
            text: Text containing code blocks

        Returns:
            Text: Formatted text with syntax highlighting
        """
        # This is a simplified implementation
        # In a real implementation, you'd parse markdown properly
        if "```python" in text:
            # Extract and highlight Python code
            try:
                code_start = text.find("```python") + 9
                code_end = text.find("```", code_start)
                if code_end > code_start:
                    code = text[code_start:code_end].strip()
                    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
                    return syntax
            except Exception:
                pass

        return Text(text)

    def _create_tool_usage_content(self, tool_name: str, args: Dict[str, Any]) -> Table:
        """
        Create formatted content for tool usage display.

        Args:
            tool_name: Name of the tool
            args: Tool arguments

        Returns:
            Table: Formatted table with tool information
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Add tool arguments to table
        for key, value in args.items():
            # Format value based on type
            if isinstance(value, dict):
                formatted_value = JSON.from_data(value)
            elif isinstance(value, (list, tuple)):
                formatted_value = ", ".join(str(v) for v in value)
            else:
                formatted_value = str(value)

            table.add_row(key, formatted_value)

        return table

    def _format_result_content(self, result: str) -> Any:
        """
        Format result content with appropriate syntax highlighting.

        Args:
            result: Result string to format

        Returns:
            Formatted content for display
        """
        # Try to detect JSON
        try:
            import json

            parsed = json.loads(result)
            return JSON.from_data(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to detect code (simple heuristic)
        if any(
            keyword in result
            for keyword in ["def ", "class ", "import ", "function", "var ", "const "]
        ):
            # Guess language based on content
            if "def " in result or "import " in result:
                return Syntax(result, "python", theme="monokai")
            elif "function" in result or "var " in result or "const " in result:
                return Syntax(result, "javascript", theme="monokai")

        # Check if it looks like markdown
        if any(marker in result for marker in ["# ", "## ", "* ", "- ", "```"]):
            return Markdown(result)

        # Default to plain text
        return Text(result, style="white")


class ServerSelector:
    """Interactive server selection interface using Textual."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the server selector.

        Args:
            console: Rich console instance, creates new one if None
        """
        self.console = console or Console()
        self._selected_server: Optional[str] = None

    def select_server(self, servers: Dict[str, MCPServerConfig]) -> str:
        """
        Interactive server selection interface.

        Args:
            servers: Available server configurations

        Returns:
            Selected server name

        Raises:
            ValueError: If no servers provided or user cancels selection
        """
        if not servers:
            raise ValueError("No servers available for selection")

        if len(servers) == 1:
            # If only one server, return it directly
            server_name = list(servers.keys())[0]
            self.console.print(f"✅ Using server: [bold cyan]{server_name}[/bold cyan]")
            return server_name

        # Display server selection menu
        self._display_server_menu(servers)

        # Get user selection
        while True:
            try:
                choice = self.console.input(
                    "\n[bold]Select server (number or name): [/bold]"
                ).strip()

                if not choice:
                    continue

                # Handle numeric selection
                if choice.isdigit():
                    index = int(choice) - 1
                    server_names = list(servers.keys())
                    if 0 <= index < len(server_names):
                        selected = server_names[index]
                        self.console.print(
                            f"✅ Selected: [bold cyan]{selected}[/bold cyan]"
                        )
                        return selected
                    else:
                        self.console.print(
                            f"[red]Invalid selection. Please choose 1-{len(servers)}[/red]"
                        )
                        continue

                # Handle name selection
                if choice in servers:
                    self.console.print(f"✅ Selected: [bold cyan]{choice}[/bold cyan]")
                    return choice

                # Handle partial name matching
                matches = [
                    name for name in servers.keys() if choice.lower() in name.lower()
                ]
                if len(matches) == 1:
                    selected = matches[0]
                    self.console.print(
                        f"✅ Selected: [bold cyan]{selected}[/bold cyan]"
                    )
                    return selected
                elif len(matches) > 1:
                    self.console.print(
                        f"[yellow]Multiple matches found: {', '.join(matches)}[/yellow]"
                    )
                    self.console.print("[yellow]Please be more specific[/yellow]")
                    continue

                # Handle quit/exit commands
                if choice.lower() in ["q", "quit", "exit", "cancel"]:
                    raise ValueError("Server selection cancelled by user")

                self.console.print(
                    f"[red]Server '{choice}' not found. Try again or type 'quit' to cancel.[/red]"
                )

            except KeyboardInterrupt:
                self.console.print("\n[red]Selection cancelled[/red]")
                raise ValueError("Server selection cancelled by user")
            except EOFError:
                self.console.print("\n[red]Selection cancelled[/red]")
                raise ValueError("Server selection cancelled by user")

    def _display_server_menu(self, servers: Dict[str, MCPServerConfig]) -> None:
        """
        Display the server selection menu.

        Args:
            servers: Available server configurations
        """
        # Create a table for server display
        table = Table(
            title="🌐 Available MCP Servers",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
        )

        table.add_column("#", style="cyan", no_wrap=True, width=3)
        table.add_column("Name", style="bold white", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Command", style="dim white")
        table.add_column("Status", style="green")

        # Add servers to table
        for i, (name, config) in enumerate(servers.items(), 1):
            # Truncate long descriptions
            description = (
                config.description[:50] + "..."
                if len(config.description) > 50
                else config.description
            )

            # Format command display
            command_display = f"{config.command} {' '.join(config.args[:2])}"
            if len(config.args) > 2:
                command_display += "..."

            # Show status (this would be enhanced with real connection status)
            status = "Available"

            table.add_row(
                str(i),
                name,
                description or "[dim]No description[/dim]",
                command_display,
                status,
            )

        self.console.print(table)

        # Show selection instructions
        instructions = Panel(
            "[bold]Selection Options:[/bold]\n"
            "• Enter server number (1, 2, 3, ...)\n"
            "• Enter server name (exact or partial match)\n"
            "• Type 'quit' or press Ctrl+C to cancel",
            title="Instructions",
            border_style="yellow",
            padding=(0, 1),
        )
        self.console.print(instructions)


class StatusDisplay:
    """Connection and operation status display."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the status display.

        Args:
            console: Rich console instance, creates new one if None
        """
        self.console = console or Console()

    def show_connection_status(
        self,
        server_name: str,
        connected: bool,
        error_message: Optional[str] = None,
        connection_time: Optional[str] = None,
        available_tools: Optional[List[str]] = None,
    ) -> None:
        """
        Display connection status with detailed information.

        Args:
            server_name: Name of the server
            connected: Connection status
            error_message: Error message if connection failed
            connection_time: Time when connection was established
            available_tools: List of available tools from the server
        """
        if connected:
            self._show_connected_status(server_name, connection_time, available_tools)
        else:
            self._show_disconnected_status(server_name, error_message)

    def show_server_info(
        self, server_config: MCPServerConfig, connection_status: Optional[bool] = None
    ) -> None:
        """
        Display detailed server information.

        Args:
            server_config: Server configuration
            connection_status: Current connection status (None if unknown)
        """
        # Create info table
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="white")

        # Add server details
        info_table.add_row("Name", server_config.name)
        info_table.add_row(
            "Description", server_config.description or "[dim]No description[/dim]"
        )
        info_table.add_row("Command", server_config.command)
        info_table.add_row("Arguments", " ".join(server_config.args))
        info_table.add_row("Timeout", f"{server_config.timeout}s")
        info_table.add_row("Retry Attempts", str(server_config.retry_attempts))

        # Add environment variables if any
        if server_config.env:
            env_vars = ", ".join([f"{k}={v}" for k, v in server_config.env.items()])
            info_table.add_row("Environment", env_vars)

        # Add connection status if available
        if connection_status is not None:
            status_text = (
                "[green]Connected[/green]"
                if connection_status
                else "[red]Disconnected[/red]"
            )
            info_table.add_row("Status", status_text)

        # Create panel with server info
        info_panel = Panel(
            info_table,
            title=f"🔧 Server: {server_config.name}",
            title_align="left",
            border_style="blue",
            padding=(0, 1),
        )

        self.console.print(info_panel)

    def show_operation_status(
        self, operation: str, status: str, details: Optional[str] = None
    ) -> None:
        """
        Display operation status.

        Args:
            operation: Name of the operation
            status: Status of the operation (success, error, in_progress, etc.)
            details: Additional details about the operation
        """
        status_styles = {
            "success": ("✅", "green"),
            "error": ("❌", "red"),
            "warning": ("⚠️", "yellow"),
            "in_progress": ("⏳", "blue"),
            "info": ("ℹ️", "blue"),
        }

        icon, color = status_styles.get(status.lower(), ("ℹ️", "blue"))

        message = f"{icon} {operation}"
        if details:
            message += f": {details}"

        self.console.print(f"[{color}]{message}[/{color}]")

    def show_tools_list(self, tools: List[ToolInfo]) -> None:
        """
        Display list of available tools.

        Args:
            tools: List of tool information objects
        """
        if not tools:
            self.console.print("[yellow]No tools available[/yellow]")
            return

        # Create tools table
        tools_table = Table(
            title=f"🛠️ Available Tools ({len(tools)})",
            show_header=True,
            header_style="bold magenta",
            border_style="green",
        )

        tools_table.add_column("Name", style="bold cyan", no_wrap=True)
        tools_table.add_column("Description", style="white")
        tools_table.add_column("Parameters", style="dim white")

        for tool in tools:
            # Format parameters
            param_count = len(tool.parameters) if tool.parameters else 0
            param_text = (
                f"{param_count} parameters" if param_count > 0 else "No parameters"
            )

            # Truncate long descriptions
            description = (
                tool.description[:60] + "..."
                if len(tool.description) > 60
                else tool.description
            )

            tools_table.add_row(
                tool.name, description or "[dim]No description[/dim]", param_text
            )

        self.console.print(tools_table)

    def show_error_with_suggestions(
        self, error_message: str, suggestions: List[str]
    ) -> None:
        """
        Display error message with actionable suggestions.

        Args:
            error_message: The error message to display
            suggestions: List of suggested solutions
        """
        # Display error
        error_text = Text(error_message, style="red")
        error_panel = Panel(
            error_text,
            title="❌ Error",
            title_align="left",
            border_style="red",
            padding=(0, 1),
        )
        self.console.print(error_panel)

        # Display suggestions if any
        if suggestions:
            suggestions_text = "\n".join(
                [f"• {suggestion}" for suggestion in suggestions]
            )
            suggestions_panel = Panel(
                suggestions_text,
                title="💡 Suggestions",
                title_align="left",
                border_style="yellow",
                padding=(0, 1),
            )
            self.console.print(suggestions_panel)

    def _show_connected_status(
        self,
        server_name: str,
        connection_time: Optional[str] = None,
        available_tools: Optional[List[str]] = None,
    ) -> None:
        """Show connected status with details."""
        status_text = f"✅ Connected to [bold cyan]{server_name}[/bold cyan]"

        if connection_time:
            status_text += f" at {connection_time}"

        self.console.print(status_text)

        if available_tools:
            tools_count = len(available_tools)
            self.console.print(
                f"🛠️ {tools_count} tools available: {', '.join(available_tools[:5])}"
            )
            if tools_count > 5:
                self.console.print(f"   ... and {tools_count - 5} more")

    def _show_disconnected_status(
        self, server_name: str, error_message: Optional[str] = None
    ) -> None:
        """Show disconnected status with error details."""
        status_text = f"❌ Failed to connect to [bold red]{server_name}[/bold red]"
        self.console.print(status_text)

        if error_message:
            error_panel = Panel(
                error_message,
                title="Error Details",
                title_align="left",
                border_style="red",
                padding=(0, 1),
            )
            self.console.print(error_panel)
