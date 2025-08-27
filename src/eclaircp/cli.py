"""
EclairCP CLI module - Main entry point for the application.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

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

    def run(self, config_path: str, server_name: Optional[str] = None, 
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
        
        # For now, show a placeholder message
        # Full session management will be implemented in task 5
        self.console.print("[bold green]EclairCP - Elegant CLI for testing MCP servers[/bold green]")
        self.console.print(f"Using configuration: {config_path}")
        
        if server_name:
            self.console.print(f"Target server: {server_name}")
        
        self.console.print("\n[yellow]Session management will be implemented in the next phase.[/yellow]")
        self.console.print("Configuration loaded successfully!")
        
        return 0


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
    
    exit_code = app.run(config, server, list_servers)
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
    except Exception as e:
        console = Console()
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())