"""
EclairCP CLI module - Main entry point for the application.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from eclaircp.config import ConfigManager, ConfigurationError


class CLIApp:
    """Main CLI application controller."""

    def __init__(self):
        """Initialize the CLI application."""
        self.console = Console()
        self.config_manager = ConfigManager()

    def show_help(self) -> None:
        """Display comprehensive help information."""
        help_text = Text()
        help_text.append("EclairCP - Elegant CLI for testing MCP servers\n\n", style="bold blue")
        
        help_text.append("DESCRIPTION:\n", style="bold")
        help_text.append("  EclairCP provides an elegant interface for testing and interacting with\n")
        help_text.append("  Model Context Protocol (MCP) servers. It features streaming conversations\n")
        help_text.append("  powered by Strands agents, real-time response display, and comprehensive\n")
        help_text.append("  server management capabilities.\n\n")
        
        help_text.append("USAGE:\n", style="bold")
        help_text.append("  eclaircp [OPTIONS]\n\n")
        
        help_text.append("OPTIONS:\n", style="bold")
        help_text.append("  -c, --config PATH    Path to configuration file (default: config.yaml)\n")
        help_text.append("  -s, --server NAME    Server name to connect to (interactive selection if not provided)\n")
        help_text.append("  -l, --list-servers   List available servers from configuration\n")
        help_text.append("  -h, --help          Show this help message and exit\n")
        help_text.append("  --version           Show version information\n\n")
        
        help_text.append("EXAMPLES:\n", style="bold")
        help_text.append("  # Start interactive session with default configuration\n")
        help_text.append("  eclaircp\n\n")
        help_text.append("  # Use a custom configuration file\n")
        help_text.append("  eclaircp -c my-servers.yaml\n\n")
        help_text.append("  # Connect directly to a specific server\n")
        help_text.append("  eclaircp -s aws-docs\n\n")
        help_text.append("  # List all configured servers with details\n")
        help_text.append("  eclaircp -l\n\n")
        help_text.append("  # Use configuration from a different directory\n")
        help_text.append("  eclaircp -c /path/to/project/mcp-config.yaml -s github\n\n")
        
        help_text.append("CONFIGURATION:\n", style="bold")
        help_text.append("  EclairCP uses YAML configuration files to define MCP servers.\n")
        help_text.append("  The configuration file should contain a 'servers' section with\n")
        help_text.append("  server definitions.\n\n")
        help_text.append("  Example configuration structure:\n", style="dim")
        help_text.append("    servers:\n", style="dim")
        help_text.append("      aws-docs:\n", style="dim")
        help_text.append("        command: \"uvx\"\n", style="dim")
        help_text.append("        args: [\"awslabs.aws-documentation-mcp-server@latest\"]\n", style="dim")
        help_text.append("        description: \"AWS Documentation Server\"\n", style="dim")
        help_text.append("        env:\n", style="dim")
        help_text.append("          FASTMCP_LOG_LEVEL: \"ERROR\"\n", style="dim")
        help_text.append("        timeout: 30\n", style="dim")
        help_text.append("        retry_attempts: 3\n\n", style="dim")
        
        help_text.append("CONFIGURATION FIELDS:\n", style="bold")
        help_text.append("  command          Command to start the MCP server (required)\n")
        help_text.append("  args             List of command arguments (required)\n")
        help_text.append("  description      Human-readable server description (optional)\n")
        help_text.append("  env              Environment variables for the server (optional)\n")
        help_text.append("  timeout          Connection timeout in seconds (default: 30)\n")
        help_text.append("  retry_attempts   Number of connection retries (default: 3)\n\n")
        
        help_text.append("COMMON MCP SERVERS:\n", style="bold")
        help_text.append("  AWS Documentation:   uvx awslabs.aws-documentation-mcp-server@latest\n")
        help_text.append("  GitHub:              uvx github-mcp-server\n")
        help_text.append("  File System:         uvx mcp-server-filesystem\n")
        help_text.append("  Strands:             uvx strands-mcp-server\n\n")
        
        help_text.append("TROUBLESHOOTING:\n", style="bold")
        help_text.append("  • Configuration file not found:\n")
        help_text.append("    - Check the file path and ensure it exists\n")
        help_text.append("    - Use -c option to specify a different config file\n")
        help_text.append("    - See examples/config.yaml for a template\n\n")
        help_text.append("  • Server connection fails:\n")
        help_text.append("    - Verify the server command and arguments are correct\n")
        help_text.append("    - Check that required dependencies (like uvx) are installed\n")
        help_text.append("    - Ensure environment variables are properly set\n")
        help_text.append("    - Try increasing the timeout value in configuration\n\n")
        help_text.append("  • Invalid YAML configuration:\n")
        help_text.append("    - Check YAML syntax (indentation, quotes, colons)\n")
        help_text.append("    - Ensure all required fields are present\n")
        help_text.append("    - Validate against the example configuration\n\n")
        help_text.append("  • Permission errors:\n")
        help_text.append("    - Ensure the configuration file is readable\n")
        help_text.append("    - Check that the MCP server command is executable\n")
        help_text.append("    - Verify environment variable access permissions\n\n")
        
        help_text.append("GETTING STARTED:\n", style="bold")
        help_text.append("  1. Create a configuration file (see examples/config.yaml)\n")
        help_text.append("  2. Install required MCP server dependencies (e.g., uvx)\n")
        help_text.append("  3. Run 'eclaircp -l' to verify your configuration\n")
        help_text.append("  4. Start a session with 'eclaircp' or 'eclaircp -s <server>'\n\n")
        
        help_text.append("For more information and examples:\n")
        help_text.append("  • GitHub: https://github.com/nag763/eclaircp\n")
        help_text.append("  • Documentation: See README.md and examples/ directory\n")
        help_text.append("  • Issues: Report bugs at https://github.com/nag763/eclaircp/issues\n")
        
        panel = Panel(help_text, title="EclairCP Help", border_style="blue")
        self.console.print(panel)

    def show_contextual_help(self, context: str = "general") -> None:
        """Display contextual help for different CLI modes and options.
        
        Args:
            context: The context for which to show help (general, config, session, etc.)
        """
        if context == "config":
            self._show_config_help()
        elif context == "session":
            self._show_session_help()
        elif context == "troubleshooting":
            self._show_troubleshooting_help()
        else:
            self.show_help()

    def _show_config_help(self) -> None:
        """Display detailed configuration help."""
        help_text = Text()
        help_text.append("Configuration Help\n\n", style="bold blue")
        
        help_text.append("CONFIGURATION FILE FORMAT:\n", style="bold")
        help_text.append("  EclairCP uses YAML configuration files with the following structure:\n\n")
        
        help_text.append("servers:\n", style="green")
        help_text.append("  server-name:\n", style="green")
        help_text.append("    command: \"command-to-run\"\n", style="green")
        help_text.append("    args: [\"arg1\", \"arg2\"]\n", style="green")
        help_text.append("    description: \"Server description\"\n", style="green")
        help_text.append("    env:\n", style="green")
        help_text.append("      VAR_NAME: \"value\"\n", style="green")
        help_text.append("    timeout: 30\n", style="green")
        help_text.append("    retry_attempts: 3\n\n", style="green")
        
        help_text.append("FIELD DESCRIPTIONS:\n", style="bold")
        help_text.append("  • command: The executable command to start the MCP server\n")
        help_text.append("  • args: List of command-line arguments for the server\n")
        help_text.append("  • description: Human-readable description (shown in server list)\n")
        help_text.append("  • env: Environment variables to set for the server process\n")
        help_text.append("  • timeout: Connection timeout in seconds (1-300, default: 30)\n")
        help_text.append("  • retry_attempts: Number of connection retries (1-10, default: 3)\n\n")
        
        help_text.append("VALIDATION RULES:\n", style="bold")
        help_text.append("  • At least one server must be configured\n")
        help_text.append("  • Server names must be unique and non-empty\n")
        help_text.append("  • Commands must be non-empty strings\n")
        help_text.append("  • Arguments are automatically trimmed of whitespace\n")
        help_text.append("  • Timeout must be between 1 and 300 seconds\n")
        help_text.append("  • Retry attempts must be between 1 and 10\n")
        
        panel = Panel(help_text, title="Configuration Help", border_style="green")
        self.console.print(panel)

    def _show_session_help(self) -> None:
        """Display session-related help."""
        help_text = Text()
        help_text.append("Session Help\n\n", style="bold blue")
        
        help_text.append("SESSION MANAGEMENT:\n", style="bold")
        help_text.append("  EclairCP creates conversational sessions with MCP servers using\n")
        help_text.append("  Strands agents for intelligent interaction and streaming responses.\n\n")
        
        help_text.append("SESSION FEATURES:\n", style="bold")
        help_text.append("  • Real-time streaming responses\n")
        help_text.append("  • Context-aware conversations\n")
        help_text.append("  • Automatic tool discovery and execution\n")
        help_text.append("  • Rich terminal formatting\n")
        help_text.append("  • Error handling and recovery\n\n")
        
        help_text.append("DURING A SESSION:\n", style="bold")
        help_text.append("  • Type your questions or requests naturally\n")
        help_text.append("  • The agent will use available MCP tools automatically\n")
        help_text.append("  • Responses stream in real-time with formatting\n")
        help_text.append("  • Use Ctrl+C to interrupt or exit the session\n\n")
        
        help_text.append("SESSION COMMANDS:\n", style="bold")
        help_text.append("  /help     Show available commands and tools\n")
        help_text.append("  /tools    List available MCP tools\n")
        help_text.append("  /status   Show connection and session status\n")
        help_text.append("  /exit     End the session\n")
        
        panel = Panel(help_text, title="Session Help", border_style="cyan")
        self.console.print(panel)

    def _show_troubleshooting_help(self) -> None:
        """Display comprehensive troubleshooting help."""
        help_text = Text()
        help_text.append("Troubleshooting Guide\n\n", style="bold blue")
        
        help_text.append("COMMON ISSUES AND SOLUTIONS:\n\n", style="bold")
        
        help_text.append("1. Configuration File Not Found\n", style="bold red")
        help_text.append("   Problem: 'Configuration file not found: config.yaml'\n")
        help_text.append("   Solutions:\n")
        help_text.append("   • Create a config.yaml file in the current directory\n")
        help_text.append("   • Use -c option to specify a different config file path\n")
        help_text.append("   • Copy examples/config.yaml as a starting template\n\n")
        
        help_text.append("2. Invalid YAML Configuration\n", style="bold red")
        help_text.append("   Problem: 'Invalid YAML in configuration file'\n")
        help_text.append("   Solutions:\n")
        help_text.append("   • Check YAML syntax (proper indentation, quotes, colons)\n")
        help_text.append("   • Validate YAML online or with a YAML linter\n")
        help_text.append("   • Ensure all required fields are present\n")
        help_text.append("   • Compare with examples/config.yaml\n\n")
        
        help_text.append("3. MCP Server Connection Fails\n", style="bold red")
        help_text.append("   Problem: Cannot connect to MCP server\n")
        help_text.append("   Solutions:\n")
        help_text.append("   • Verify the server command exists and is executable\n")
        help_text.append("   • Check that uvx is installed (pip install uv)\n")
        help_text.append("   • Ensure environment variables are properly set\n")
        help_text.append("   • Try increasing timeout in configuration\n")
        help_text.append("   • Test the server command manually\n\n")
        
        help_text.append("4. Permission Errors\n", style="bold red")
        help_text.append("   Problem: Permission denied errors\n")
        help_text.append("   Solutions:\n")
        help_text.append("   • Ensure configuration file is readable\n")
        help_text.append("   • Check execute permissions on MCP server commands\n")
        help_text.append("   • Verify environment variable access\n")
        help_text.append("   • Run with appropriate user permissions\n\n")
        
        help_text.append("5. Dependency Issues\n", style="bold red")
        help_text.append("   Problem: Missing dependencies or import errors\n")
        help_text.append("   Solutions:\n")
        help_text.append("   • Install uv and uvx: pip install uv\n")
        help_text.append("   • Update Python to version 3.10 or higher\n")
        help_text.append("   • Install EclairCP dependencies: uv sync\n")
        help_text.append("   • Check virtual environment activation\n\n")
        
        help_text.append("DIAGNOSTIC COMMANDS:\n", style="bold")
        help_text.append("  eclaircp -l                    # List configured servers\n")
        help_text.append("  eclaircp --version             # Check EclairCP version\n")
        help_text.append("  uvx --version                  # Check uvx installation\n")
        help_text.append("  python --version               # Check Python version\n\n")
        
        help_text.append("GETTING HELP:\n", style="bold")
        help_text.append("  • Check the README.md file for detailed documentation\n")
        help_text.append("  • Review examples/config.yaml for configuration examples\n")
        help_text.append("  • Report issues: https://github.com/nag763/eclaircp/issues\n")
        help_text.append("  • Include error messages and configuration when reporting bugs\n")
        
        panel = Panel(help_text, title="Troubleshooting Guide", border_style="red")
        self.console.print(panel)

    def list_servers(self, config_path: str) -> int:
        """List available servers from configuration.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            config = self.config_manager.load_config(config_path)
            
            if not config.servers:
                self.console.print("[yellow]No servers configured.[/yellow]")
                return 1
            
            self.console.print("\n[bold blue]Available MCP Servers:[/bold blue]\n")
            
            for name, server in config.servers.items():
                server_info = Text()
                server_info.append(f"• {name}", style="bold green")
                if server.description:
                    server_info.append(f" - {server.description}")
                server_info.append(f"\n  Command: {server.command} {' '.join(server.args)}", style="dim")
                if server.env:
                    server_info.append(f"\n  Environment: {len(server.env)} variables", style="dim")
                
                self.console.print(server_info)
                self.console.print()
            
            return 0
            
        except ConfigurationError as e:
            self.console.print(f"[red]Configuration error: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {e}[/red]")
            return 1

    def validate_config_file(self, config_path: str) -> bool:
        """Validate that configuration file exists and is readable.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if valid, False otherwise
        """
        if not os.path.exists(config_path):
            self.console.print(f"[red]Configuration file not found: {config_path}[/red]")
            self.console.print("\n[yellow]To get started, create a configuration file.[/yellow]")
            self.console.print("See examples/config.yaml for a template.")
            return False
        
        try:
            self.config_manager.load_config(config_path)
            return True
        except ConfigurationError as e:
            self.console.print(f"[red]Configuration error: {e}[/red]")
            return False

    async def run(self, config_path: str, server_name: Optional[str] = None, 
            list_servers: bool = False) -> int:
        """Main entry point for CLI execution.
        
        Args:
            config_path: Path to configuration file
            server_name: Optional server name to connect to
            list_servers: Whether to list servers and exit
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Handle list servers command
        if list_servers:
            return self.list_servers(config_path)
        
        # Validate configuration file
        if not self.validate_config_file(config_path):
            return 1
        
        try:
            # Load configuration
            config = self.config_manager.load_config(config_path)
            
            # Start the complete user workflow
            return await self._run_interactive_session(config, server_name)
            
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {e}[/red]")
            return 1

    async def _run_interactive_session(self, config, server_name: Optional[str] = None) -> int:
        """Run the complete interactive session workflow.
        
        Args:
            config: Loaded configuration
            server_name: Optional server name to connect to
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        from .mcp import MCPClientManager
        from .session import SessionManager
        from .ui import ServerSelector, StreamingDisplay, StatusDisplay
        from .config import SessionConfig
        
        # Initialize components
        mcp_client = MCPClientManager()
        server_selector = ServerSelector(self.console)
        streaming_display = StreamingDisplay(self.console)
        status_display = StatusDisplay(self.console)
        
        try:
            # Welcome message
            self.console.print("[bold green]🌟 EclairCP - Elegant CLI for testing MCP servers[/bold green]")
            self.console.print()  # Remove config_path reference as it's not available in this scope
            
            # Server selection flow
            selected_server_name = await self._handle_server_selection(
                config, server_name, server_selector, status_display
            )
            
            if not selected_server_name:
                return 1
            
            selected_server_config = config.servers[selected_server_name]
            
            # Connection flow
            if not await self._handle_server_connection(
                mcp_client, selected_server_config, status_display
            ):
                return 1
            
            # Session flow
            return await self._handle_conversation_session(
                mcp_client, selected_server_name, streaming_display, status_display
            )
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Session interrupted by user[/yellow]")
            return 0
        except Exception as e:
            self.console.print(f"[red]Session error: {e}[/red]")
            return 1
        finally:
            # Cleanup
            if mcp_client.is_connected():
                await mcp_client.disconnect()

    async def _handle_server_selection(self, config, server_name: Optional[str], 
                                     server_selector: 'ServerSelector', 
                                     status_display: 'StatusDisplay') -> Optional[str]:
        """Handle server selection flow.
        
        Args:
            config: Configuration object
            server_name: Optional pre-selected server name
            server_selector: Server selector UI component
            status_display: Status display component
            
        Returns:
            Selected server name or None if selection failed
        """
        try:
            if server_name:
                # Validate provided server name
                if server_name not in config.servers:
                    self.console.print(f"[red]Server '{server_name}' not found in configuration[/red]")
                    available_servers = list(config.servers.keys())
                    self.console.print(f"Available servers: {', '.join(available_servers)}")
                    return None
                
                self.console.print(f"✅ Using specified server: [bold cyan]{server_name}[/bold cyan]")
                return server_name
            else:
                # Interactive server selection
                self.console.print("[bold blue]📡 Server Selection[/bold blue]")
                return server_selector.select_server(config.servers)
                
        except ValueError as e:
            self.console.print(f"[red]Server selection error: {e}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Unexpected error during server selection: {e}[/red]")
            return None

    async def _handle_server_connection(self, mcp_client: 'MCPClientManager', 
                                      server_config: 'MCPServerConfig',
                                      status_display: 'StatusDisplay') -> bool:
        """Handle server connection flow.
        
        Args:
            mcp_client: MCP client manager
            server_config: Server configuration
            status_display: Status display component
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.console.print(f"\n[bold blue]🔌 Connecting to {server_config.name}[/bold blue]")
            
            # Show server info
            status_display.show_server_info(server_config)
            
            # Show loading indicator
            with self.console.status(f"[bold green]Connecting to {server_config.name}..."):
                success = await mcp_client.connect(server_config)
            
            if success:
                # Show connection success
                connection_status = mcp_client.get_connection_status()
                status_display.show_connection_status(
                    server_config.name,
                    True,
                    connection_time=connection_status.connection_time.isoformat() if connection_status.connection_time else None,
                    available_tools=connection_status.available_tools
                )
                
                # Show available tools
                tools = await mcp_client.list_tools()
                if tools:
                    status_display.show_tools_list(tools)
                
                return True
            else:
                connection_status = mcp_client.get_connection_status()
                status_display.show_connection_status(
                    server_config.name,
                    False,
                    error_message=connection_status.error_message
                )
                return False
                
        except Exception as e:
            self.console.print(f"[red]Connection failed: {e}[/red]")
            return False

    async def _handle_conversation_session(self, mcp_client: 'MCPClientManager',
                                         server_name: str,
                                         streaming_display: 'StreamingDisplay',
                                         status_display: 'StatusDisplay') -> int:
        """Handle the conversation session flow.
        
        Args:
            mcp_client: Connected MCP client
            server_name: Name of connected server
            streaming_display: Streaming display component
            status_display: Status display component
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        from .session import SessionManager, StreamingHandler
        from .config import SessionConfig
        
        try:
            # Create session configuration
            session_config = SessionConfig(server_name=server_name)
            
            # Initialize session manager
            session_manager = SessionManager(mcp_client, session_config)
            
            # Start session
            self.console.print(f"\n[bold blue]💬 Starting conversation session[/bold blue]")
            
            with self.console.status("[bold green]Initializing session..."):
                await session_manager.start_session()
            
            self.console.print("[green]✅ Session started successfully![/green]")
            self.console.print()
            
            # Show session info
            session_info = session_manager.get_session_info()
            self._show_session_info(session_info)
            
            # Start conversation loop
            return await self._conversation_loop(session_manager, streaming_display)
            
        except Exception as e:
            self.console.print(f"[red]Session initialization failed: {e}[/red]")
            return 1
        finally:
            # Cleanup session
            if 'session_manager' in locals():
                await session_manager.end_session()

    def _show_session_info(self, session_info: Dict[str, Any]) -> None:
        """Show session information.
        
        Args:
            session_info: Session information dictionary
        """
        from rich.table import Table
        
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Server", session_info.get('server_name', 'Unknown'))
        info_table.add_row("Model", session_info.get('model', 'Unknown'))
        info_table.add_row("Tools Available", str(session_info.get('tools_loaded', 0)))
        info_table.add_row("Status", "Active" if session_info.get('active') else "Inactive")
        
        from rich.panel import Panel
        info_panel = Panel(
            info_table,
            title="📊 Session Information",
            title_align="left",
            border_style="blue",
            padding=(0, 1),
        )
        
        self.console.print(info_panel)
        self.console.print()

    async def _conversation_loop(self, session_manager: 'SessionManager',
                               streaming_display: 'StreamingDisplay') -> int:
        """Run the main conversation loop.
        
        Args:
            session_manager: Session manager instance
            streaming_display: Streaming display component
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        self.console.print("[bold cyan]💭 Ready for conversation![/bold cyan]")
        self.console.print("[dim]Type your message and press Enter. Use '/exit' to quit, '/help' for commands.[/dim]")
        self.console.print()
        
        try:
            while True:
                # Get user input
                try:
                    user_input = self.console.input("[bold green]You:[/bold green] ").strip()
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[yellow]Goodbye![/yellow]")
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.startswith('/'):
                    if await self._handle_session_command(user_input, session_manager):
                        break  # Exit command
                    continue
                
                # Process user input through session
                self.console.print("\n[bold blue]Assistant:[/bold blue]")
                
                try:
                    # Stream the response
                    async for event in session_manager.process_input(user_input):
                        self._handle_stream_event(event, streaming_display)
                    
                    self.console.print("\n")
                    
                except Exception as e:
                    self.console.print(f"[red]Error processing input: {e}[/red]")
                    continue
            
            return 0
            
        except Exception as e:
            self.console.print(f"[red]Conversation error: {e}[/red]")
            return 1

    async def _handle_session_command(self, command: str, session_manager: 'SessionManager') -> bool:
        """Handle session commands.
        
        Args:
            command: Command string starting with '/'
            session_manager: Session manager instance
            
        Returns:
            True if should exit session, False otherwise
        """
        command = command.lower().strip()
        
        if command in ['/exit', '/quit', '/q']:
            self.console.print("[yellow]Ending session...[/yellow]")
            return True
        
        elif command in ['/help', '/h']:
            self._show_session_help()
        
        elif command in ['/status', '/info']:
            session_info = session_manager.get_session_info()
            self._show_session_info(session_info)
        
        elif command in ['/tools']:
            if session_manager.mcp_client.is_connected():
                tools = await session_manager.mcp_client.list_tools()
                from .ui import StatusDisplay
                status_display = StatusDisplay(self.console)
                status_display.show_tools_list(tools)
            else:
                self.console.print("[red]Not connected to any server[/red]")
        
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[dim]Use '/help' to see available commands[/dim]")
        
        return False

    def _show_session_help(self) -> None:
        """Show session help commands."""
        from rich.table import Table
        from rich.panel import Panel
        
        help_table = Table(show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        
        help_table.add_row("/help, /h", "Show this help message")
        help_table.add_row("/status, /info", "Show session and connection status")
        help_table.add_row("/tools", "List available MCP tools")
        help_table.add_row("/exit, /quit, /q", "End the session")
        
        help_panel = Panel(
            help_table,
            title="💡 Session Commands",
            title_align="left",
            border_style="yellow",
            padding=(0, 1),
        )
        
        self.console.print(help_panel)

    def _handle_stream_event(self, event: 'StreamEvent', streaming_display: 'StreamingDisplay') -> None:
        """Handle streaming events from session.
        
        Args:
            event: Stream event to handle
            streaming_display: Streaming display component
        """
        from .config import StreamEventType
        
        if event.event_type == StreamEventType.TEXT:
            streaming_display.stream_text_instant(str(event.data))
        
        elif event.event_type == StreamEventType.TOOL_USE:
            if isinstance(event.data, dict):
                tool_name = event.data.get('tool_name', 'Unknown')
                args = event.data.get('arguments', {})
                result = event.data.get('result')
                
                streaming_display.show_tool_usage(tool_name, args)
                if result:
                    streaming_display.show_tool_result(tool_name, result)
        
        elif event.event_type == StreamEventType.ERROR:
            streaming_display.show_error(str(event.data))
        
        elif event.event_type == StreamEventType.STATUS:
            streaming_display.show_status(str(event.data), "info")
        
        elif event.event_type == StreamEventType.COMPLETE:
            # Just log completion, don't display anything
            pass


@click.command()
@click.option(
    '-c', '--config',
    default='config.yaml',
    type=click.Path(),
    help='Path to configuration file (default: config.yaml)'
)
@click.option(
    '-s', '--server',
    help='Server name to connect to (interactive selection if not provided)'
)
@click.option(
    '-l', '--list-servers',
    is_flag=True,
    help='List available servers from configuration'
)
@click.option(
    '--help-config',
    is_flag=True,
    help='Show detailed configuration help'
)
@click.option(
    '--help-session',
    is_flag=True,
    help='Show session management help'
)
@click.option(
    '--help-troubleshooting',
    is_flag=True,
    help='Show troubleshooting guide'
)
@click.option(
    '--version',
    is_flag=True,
    help='Show version information'
)
@click.help_option('-h', '--help')
def cli(config: str, server: Optional[str], list_servers: bool, 
        help_config: bool, help_session: bool, help_troubleshooting: bool,
        version: bool) -> None:
    """EclairCP - Elegant CLI for testing MCP servers.
    
    A Python-based tool for interactive testing and validation of Model Context
    Protocol servers with streaming responses powered by Strands agents.
    """
    app = CLIApp()
    
    # Handle help options first
    if help_config:
        app.show_contextual_help("config")
        return
    
    if help_session:
        app.show_contextual_help("session")
        return
    
    if help_troubleshooting:
        app.show_contextual_help("troubleshooting")
        return
    
    if version:
        click.echo("EclairCP version 0.1.0")
        return
    
    # Run the async application
    exit_code = asyncio.run(app.run(config, server, list_servers))
    sys.exit(exit_code)


def main(args: List[str] = None) -> int:
    """
    Main entry point for the EclairCP CLI application.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        if args is None:
            cli()
        else:
            cli(args)
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 0
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 0
    except Exception as e:
        console = Console()
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())