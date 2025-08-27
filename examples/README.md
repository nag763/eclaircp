# EclairCP Examples

This directory contains example configuration files and usage scenarios for EclairCP.

## Configuration File

The `config.yaml` file shows how to configure multiple MCP servers for testing:

- **aws-docs**: AWS Documentation MCP Server
- **github**: GitHub MCP Server (requires GITHUB_TOKEN environment variable)
- **strands**: Strands MCP Server

## Usage

1. Copy the example configuration to your preferred location:
   ```bash
   cp examples/config.yaml ~/.eclaircp/config.yaml
   ```

2. Set up required environment variables:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

3. Run EclairCP with the configuration:
   ```bash
   eclaircp --config ~/.eclaircp/config.yaml
   ```

## Environment Variables

Some MCP servers require environment variables:

- `GITHUB_TOKEN`: Required for the GitHub MCP server
- `FASTMCP_LOG_LEVEL`: Controls logging level for MCP servers

## Server Configuration Options

Each server configuration supports:

- `command`: The command to run the MCP server
- `args`: Arguments to pass to the command
- `description`: Human-readable description
- `env`: Environment variables to set
- `timeout`: Connection timeout in seconds (default: 30)
- `retry_attempts`: Number of retry attempts (default: 3)