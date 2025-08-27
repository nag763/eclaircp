"""
Tests for the CLI module.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from eclaircp.cli import CLIApp, cli, main
from eclaircp.config import ConfigFile, MCPServerConfig


class TestCLIApp:
    """Test cases for CLIApp class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = CLIApp()

    def test_init(self):
        """Test CLIApp initialization."""
        assert self.app.console is not None
        assert self.app.config_manager is not None

    def test_show_help(self, capsys):
        """Test help display functionality."""
        self.app.show_help()
        captured = capsys.readouterr()
        assert "EclairCP - Elegant CLI for testing MCP servers" in captured.out
        assert "DESCRIPTION:" in captured.out
        assert "USAGE:" in captured.out
        assert "OPTIONS:" in captured.out
        assert "EXAMPLES:" in captured.out
        assert "CONFIGURATION:" in captured.out
        assert "TROUBLESHOOTING:" in captured.out
        assert "GETTING STARTED:" in captured.out

    def test_show_contextual_help_config(self, capsys):
        """Test contextual help for configuration."""
        self.app.show_contextual_help("config")
        captured = capsys.readouterr()
        assert "Configuration Help" in captured.out
        assert "CONFIGURATION FILE FORMAT:" in captured.out
        assert "FIELD DESCRIPTIONS:" in captured.out
        assert "VALIDATION RULES:" in captured.out

    def test_show_contextual_help_session(self, capsys):
        """Test contextual help for sessions."""
        self.app.show_contextual_help("session")
        captured = capsys.readouterr()
        assert "Session Help" in captured.out
        assert "SESSION MANAGEMENT:" in captured.out
        assert "SESSION FEATURES:" in captured.out
        assert "SESSION COMMANDS:" in captured.out

    def test_show_contextual_help_troubleshooting(self, capsys):
        """Test contextual help for troubleshooting."""
        self.app.show_contextual_help("troubleshooting")
        captured = capsys.readouterr()
        assert "Troubleshooting Guide" in captured.out
        assert "COMMON ISSUES AND SOLUTIONS:" in captured.out
        assert "DIAGNOSTIC COMMANDS:" in captured.out
        assert "GETTING HELP:" in captured.out

    def test_show_contextual_help_general(self, capsys):
        """Test contextual help with general context."""
        self.app.show_contextual_help("general")
        captured = capsys.readouterr()
        assert "EclairCP - Elegant CLI for testing MCP servers" in captured.out

    def test_validate_config_file_missing(self, capsys):
        """Test validation with missing config file."""
        result = self.app.validate_config_file("nonexistent.yaml")
        assert result is False
        captured = capsys.readouterr()
        assert "Configuration file not found" in captured.out

    def test_validate_config_file_valid(self):
        """Test validation with valid config file."""
        # Create a temporary valid config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
    description: "Test server"
""")
            temp_path = f.name

        try:
            result = self.app.validate_config_file(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_list_servers_no_config(self, capsys):
        """Test listing servers with missing config."""
        result = self.app.list_servers("nonexistent.yaml")
        assert result == 1
        captured = capsys.readouterr()
        assert "Configuration error" in captured.out

    def test_list_servers_empty_config(self, capsys):
        """Test listing servers with empty server list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("servers: {}")
            temp_path = f.name

        try:
            result = self.app.list_servers(temp_path)
            assert result == 1
            captured = capsys.readouterr()
            # The validation error should be caught and displayed as a configuration error
            assert "Configuration error" in captured.out
        finally:
            os.unlink(temp_path)

    def test_list_servers_with_servers(self, capsys):
        """Test listing servers with valid configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
    description: "Test server"
  another-server:
    command: "uvx"
    args: ["some-package"]
    description: "Another test server"
""")
            temp_path = f.name

        try:
            result = self.app.list_servers(temp_path)
            assert result == 0
            captured = capsys.readouterr()
            assert "Available MCP Servers:" in captured.out
            assert "test-server" in captured.out
            assert "another-server" in captured.out
        finally:
            os.unlink(temp_path)

    def test_run_list_servers_flag(self):
        """Test run method with list_servers flag."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
""")
            temp_path = f.name

        try:
            result = self.app.run(temp_path, list_servers=True)
            assert result == 0
        finally:
            os.unlink(temp_path)

    def test_run_invalid_config(self, capsys):
        """Test run method with invalid config."""
        result = self.app.run("nonexistent.yaml")
        assert result == 1
        captured = capsys.readouterr()
        assert "Configuration file not found" in captured.out

    def test_run_valid_config(self, capsys):
        """Test run method with valid config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
""")
            temp_path = f.name

        try:
            result = self.app.run(temp_path)
            assert result == 0
            captured = capsys.readouterr()
            assert "EclairCP - Elegant CLI for testing MCP servers" in captured.out
            assert "Configuration loaded successfully!" in captured.out
        finally:
            os.unlink(temp_path)

    def test_run_with_server_name(self, capsys):
        """Test run method with specific server name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
""")
            temp_path = f.name

        try:
            result = self.app.run(temp_path, server_name="test-server")
            assert result == 0
            captured = capsys.readouterr()
            assert "Target server: test-server" in captured.out
        finally:
            os.unlink(temp_path)


class TestClickCLI:
    """Test cases for Click CLI interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "EclairCP - Elegant CLI for testing MCP servers" in result.output
        assert "Usage:" in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "EclairCP version 0.1.0" in result.output

    def test_cli_list_servers_missing_config(self):
        """Test CLI list servers with missing config."""
        result = self.runner.invoke(cli, ['-l', '-c', 'nonexistent.yaml'])
        assert result.exit_code == 1

    def test_cli_list_servers_valid_config(self):
        """Test CLI list servers with valid config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
    description: "Test server"
""")
            temp_path = f.name

        try:
            result = self.runner.invoke(cli, ['-l', '-c', temp_path])
            assert result.exit_code == 0
            assert "test-server" in result.output
        finally:
            os.unlink(temp_path)

    def test_cli_with_config_and_server(self):
        """Test CLI with config and server options."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
servers:
  test-server:
    command: "echo"
    args: ["hello"]
""")
            temp_path = f.name

        try:
            result = self.runner.invoke(cli, ['-c', temp_path, '-s', 'test-server'])
            assert result.exit_code == 0
        finally:
            os.unlink(temp_path)

    def test_cli_help_config(self):
        """Test CLI configuration help command."""
        result = self.runner.invoke(cli, ['--help-config'])
        assert result.exit_code == 0
        assert "Configuration Help" in result.output
        assert "CONFIGURATION FILE FORMAT:" in result.output

    def test_cli_help_session(self):
        """Test CLI session help command."""
        result = self.runner.invoke(cli, ['--help-session'])
        assert result.exit_code == 0
        assert "Session Help" in result.output
        assert "SESSION MANAGEMENT:" in result.output

    def test_cli_help_troubleshooting(self):
        """Test CLI troubleshooting help command."""
        result = self.runner.invoke(cli, ['--help-troubleshooting'])
        assert result.exit_code == 0
        assert "Troubleshooting Guide" in result.output
        assert "COMMON ISSUES AND SOLUTIONS:" in result.output


class TestHelpContent:
    """Test cases for help content accuracy and completeness."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = CLIApp()

    def test_help_content_completeness(self, capsys):
        """Test that help content includes all required sections."""
        self.app.show_help()
        captured = capsys.readouterr()
        
        # Check all major sections are present
        required_sections = [
            "DESCRIPTION:",
            "USAGE:",
            "OPTIONS:",
            "EXAMPLES:",
            "CONFIGURATION:",
            "CONFIGURATION FIELDS:",
            "COMMON MCP SERVERS:",
            "TROUBLESHOOTING:",
            "GETTING STARTED:"
        ]
        
        for section in required_sections:
            assert section in captured.out, f"Missing section: {section}"

    def test_config_help_accuracy(self, capsys):
        """Test that configuration help matches actual validation rules."""
        self.app._show_config_help()
        captured = capsys.readouterr()
        
        # Check that help mentions actual validation constraints
        assert "1-300" in captured.out  # timeout range
        assert "1-10" in captured.out   # retry attempts range
        assert "At least one server must be configured" in captured.out
        assert "non-empty strings" in captured.out

    def test_troubleshooting_help_coverage(self, capsys):
        """Test that troubleshooting help covers common error scenarios."""
        self.app._show_troubleshooting_help()
        captured = capsys.readouterr()
        
        # Check coverage of common issues
        common_issues = [
            "Configuration File Not Found",
            "Invalid YAML Configuration", 
            "MCP Server Connection Fails",
            "Permission Errors",
            "Dependency Issues"
        ]
        
        for issue in common_issues:
            assert issue in captured.out, f"Missing troubleshooting for: {issue}"

    def test_session_help_commands(self, capsys):
        """Test that session help includes all available commands."""
        self.app._show_session_help()
        captured = capsys.readouterr()
        
        # Check that session commands are documented
        session_commands = ["/help", "/tools", "/status", "/exit"]
        for command in session_commands:
            assert command in captured.out, f"Missing session command: {command}"


class TestMainFunction:
    """Test cases for main function."""

    def test_main_no_args(self):
        """Test main function with no arguments."""
        with patch('eclaircp.cli.cli') as mock_cli:
            main()
            mock_cli.assert_called_once()

    def test_main_with_args(self):
        """Test main function with arguments."""
        with patch('eclaircp.cli.cli') as mock_cli:
            main(['--version'])
            mock_cli.assert_called_once_with(['--version'])

    def test_main_exception_handling(self):
        """Test main function exception handling."""
        with patch('eclaircp.cli.cli', side_effect=Exception("Test error")):
            result = main()
            assert result == 1