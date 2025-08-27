#!/usr/bin/env python3
"""
EclairCP Demonstration Script

This script demonstrates the key capabilities of EclairCP, an elegant CLI tool
for testing MCP servers with streaming responses powered by Strands agents.

This demo showcases:
1. Configuration management with multiple MCP servers
2. Interactive server selection
3. Streaming conversation interface
4. Tool usage and MCP server integration
5. Error handling and recovery

Usage:
    python demo.py
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from eclaircp.config import ConfigManager, MCPServerConfig
from eclaircp.mcp import MCPClientManager
from eclaircp.session import SessionManager
from eclaircp.ui import StreamingDisplay, ServerSelector
from eclaircp.exceptions import EclairCPError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align


class EclairCPDemo:
    """Demonstration class for EclairCP capabilities."""
    
    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        self.mcp_client = MCPClientManager()
        self.display = StreamingDisplay()
        self.server_selector = ServerSelector()
        
    def print_header(self):
        """Print the demo header."""
        header_text = Text("EclairCP Demonstration", style="bold magenta")
        subtitle_text = Text("Elegant CLI for testing MCP servers", style="italic cyan")
        
        header_panel = Panel(
            Align.center(f"{header_text}\n{subtitle_text}"),
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print(header_panel)
        self.console.print()
        
    def print_section(self, title: str, description: str):
        """Print a demo section header."""
        self.console.print(f"\n[bold blue]🔹 {title}[/bold blue]")
        self.console.print(f"[dim]{description}[/dim]")
        self.console.print()
        
    def simulate_typing(self, text: str, delay: float = 0.03):
        """Simulate typing effect for demo purposes."""
        for char in text:
            self.console.print(char, end="", style="green")
            time.sleep(delay)
        self.console.print()
        
    def demo_configuration_management(self):
        """Demonstrate configuration management capabilities."""
        self.print_section(
            "Configuration Management",
            "EclairCP uses YAML configuration files to manage multiple MCP servers"
        )
        
        # Create a demo configuration
        demo_config = {
            "servers": {
                "aws-docs": {
                    "command": "uvx",
                    "args": ["awslabs.aws-documentation-mcp-server@latest"],
                    "description": "AWS Documentation MCP Server",
                    "env": {"FASTMCP_LOG_LEVEL": "ERROR"},
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "github": {
                    "command": "uvx", 
                    "args": ["github-mcp-server"],
                    "description": "GitHub MCP Server",
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
                    "timeout": 45,
                    "retry_attempts": 3
                },
                "strands": {
                    "command": "uvx",
                    "args": ["strands-mcp-server"],
                    "description": "Strands MCP Server",
                    "timeout": 30,
                    "retry_attempts": 2
                }
            },
            "default_session": {
                "server_name": "aws-docs",
                "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "system_prompt": "You are a helpful assistant for testing MCP servers.",
                "max_context_length": 100000
            }
        }
        
        try:
            # Validate the configuration using Pydantic
            config_file = self.config_manager.validate_config(demo_config)
            
            self.console.print("[green]✅ Configuration validated successfully![/green]")
            self.console.print(f"[dim]Found {len(config_file.servers)} configured servers:[/dim]")
            
            for name, server in config_file.servers.items():
                self.console.print(f"  • [cyan]{name}[/cyan]: {server.description}")
                
        except Exception as e:
            self.console.print(f"[red]❌ Configuration error: {e}[/red]")
            
    def demo_server_selection(self):
        """Demonstrate interactive server selection."""
        self.print_section(
            "Interactive Server Selection",
            "Users can select from configured MCP servers with an elegant interface"
        )
        
        # Simulate server selection interface
        servers = {
            "aws-docs": "AWS Documentation MCP Server - Search and read AWS documentation",
            "github": "GitHub MCP Server - Interact with GitHub repositories, issues, and PRs", 
            "strands": "Strands MCP Server - Access Strands documentation and development tools"
        }
        
        self.console.print("[bold]Available MCP Servers:[/bold]")
        for i, (name, desc) in enumerate(servers.items(), 1):
            self.console.print(f"  {i}. [cyan]{name}[/cyan] - {desc}")
            
        self.console.print("\n[dim]In the real application, users can interactively select servers...[/dim]")
        self.console.print("[green]Selected: aws-docs[/green]")
        
    def demo_streaming_interface(self):
        """Demonstrate streaming response interface."""
        self.print_section(
            "Streaming Response Interface", 
            "Real-time streaming responses powered by Strands agents"
        )
        
        # Simulate a conversation
        user_query = "How do I create an S3 bucket with versioning enabled?"
        self.console.print(f"[bold blue]User:[/bold blue] {user_query}")
        self.console.print()
        
        # Simulate streaming response
        response_parts = [
            "I'll help you learn about creating S3 buckets with versioning. ",
            "Let me search the AWS documentation for the most current information...\n\n",
            "[Tool: search_documentation]\n",
            "Arguments: {\"search_phrase\": \"create S3 bucket versioning\"}\n\n",
            "📚 Based on the AWS documentation, here's how to create an S3 bucket with versioning:\n\n",
            "1. **Using AWS Console:**\n",
            "   - Navigate to the S3 console\n",
            "   - Click 'Create bucket'\n",
            "   - Configure bucket settings\n",
            "   - Enable versioning in the 'Properties' tab\n\n",
            "2. **Using AWS CLI:**\n",
            "   ```bash\n",
            "   aws s3 mb s3://your-bucket-name\n",
            "   aws s3api put-bucket-versioning --bucket your-bucket-name --versioning-configuration Status=Enabled\n",
            "   ```\n\n",
            "3. **Using CloudFormation:**\n",
            "   ```yaml\n",
            "   Resources:\n",
            "     MyBucket:\n",
            "       Type: AWS::S3::Bucket\n",
            "       Properties:\n",
            "         VersioningConfiguration:\n",
            "           Status: Enabled\n",
            "   ```\n\n",
            "Versioning helps protect against accidental deletion and allows you to retrieve previous versions of objects."
        ]
        
        self.console.print("[bold green]Assistant:[/bold green]", end=" ")
        
        for part in response_parts:
            if part.startswith("[Tool:"):
                self.console.print(f"\n[yellow]{part}[/yellow]", end="")
            elif part.startswith("Arguments:"):
                self.console.print(f"[dim]{part}[/dim]", end="")
            else:
                for char in part:
                    self.console.print(char, end="")
                    time.sleep(0.01)  # Simulate streaming
                    
        self.console.print("\n")
        
    def demo_error_handling(self):
        """Demonstrate error handling capabilities."""
        self.print_section(
            "Error Handling & Recovery",
            "Elegant error messages with actionable suggestions"
        )
        
        # Simulate various error scenarios
        error_scenarios = [
            {
                "error": "Connection timeout to MCP server",
                "suggestion": "Try increasing the timeout value in your configuration or check server availability"
            },
            {
                "error": "Invalid YAML configuration",
                "suggestion": "Check YAML syntax and ensure all required fields are present"
            },
            {
                "error": "Missing environment variable: GITHUB_TOKEN",
                "suggestion": "Set the GITHUB_TOKEN environment variable with your GitHub personal access token"
            }
        ]
        
        for scenario in error_scenarios:
            self.console.print(f"[red]❌ Error:[/red] {scenario['error']}")
            self.console.print(f"[yellow]💡 Suggestion:[/yellow] {scenario['suggestion']}")
            self.console.print()
            
    def demo_tool_integration(self):
        """Demonstrate MCP tool integration."""
        self.print_section(
            "MCP Tool Integration",
            "Seamless integration with MCP server tools through Strands agents"
        )
        
        # Show available tools from different servers
        server_tools = {
            "aws-docs": [
                "read_documentation - Read specific AWS documentation pages",
                "search_documentation - Search AWS documentation",
                "recommend - Get content recommendations"
            ],
            "github": [
                "create_issue - Create GitHub issues",
                "list_repositories - List user repositories", 
                "get_pull_request - Get pull request details",
                "search_code - Search code across repositories"
            ],
            "strands": [
                "quickstart - Get Strands quickstart documentation",
                "model_providers - Learn about model providers",
                "agent_tools - Documentation on agent tools"
            ]
        }
        
        for server, tools in server_tools.items():
            self.console.print(f"[bold cyan]{server}[/bold cyan] available tools:")
            for tool in tools:
                self.console.print(f"  • {tool}")
            self.console.print()
            
    def demo_development_workflow(self):
        """Demonstrate development workflow."""
        self.print_section(
            "Development Workflow",
            "How EclairCP fits into MCP server development and testing"
        )
        
        workflow_steps = [
            "1. Configure your MCP servers in config.yaml",
            "2. Start EclairCP and select a server to test",
            "3. Interact with the server through natural conversation",
            "4. Test tool functionality and edge cases",
            "5. Validate server responses and behavior",
            "6. Debug issues with detailed error messages"
        ]
        
        for step in workflow_steps:
            self.console.print(f"[green]{step}[/green]")
            time.sleep(0.5)
            
    async def run_demo(self):
        """Run the complete demonstration."""
        self.print_header()
        
        self.console.print("[bold yellow]Welcome to the EclairCP demonstration![/bold yellow]")
        self.console.print("[dim]This demo showcases the key features of EclairCP without requiring actual MCP server connections.[/dim]")
        self.console.print()
        
        # Run demonstration sections
        self.demo_configuration_management()
        time.sleep(2)
        
        self.demo_server_selection()
        time.sleep(2)
        
        self.demo_streaming_interface()
        time.sleep(2)
        
        self.demo_tool_integration()
        time.sleep(2)
        
        self.demo_error_handling()
        time.sleep(2)
        
        self.demo_development_workflow()
        time.sleep(2)
        
        # Conclusion
        self.print_section(
            "Conclusion",
            "EclairCP provides an elegant, powerful interface for MCP server testing"
        )
        
        conclusion_text = """
EclairCP combines:
• Modern Python development practices with UV and Pydantic
• Elegant terminal UI with Rich and Textual
• Powerful AI conversations with Strands agents
• Robust MCP server integration
• Comprehensive error handling and recovery

Perfect for developers working with Model Context Protocol servers!
        """
        
        conclusion_panel = Panel(
            conclusion_text.strip(),
            title="[bold green]EclairCP Features[/bold green]",
            border_style="green"
        )
        
        self.console.print(conclusion_panel)
        self.console.print()
        self.console.print("[bold blue]Thank you for watching the EclairCP demonstration![/bold blue]")
        self.console.print("[dim]Visit https://github.com/nag763/eclaircp for more information.[/dim]")


async def main():
    """Main demo function."""
    demo = EclairCPDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())