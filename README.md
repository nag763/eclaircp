# EclairCP

**Elegant CLI for testing MCP servers**

EclairCP is a Python-based CLI tool designed to test and interact with remote Model Context Protocol (MCP) servers. The tool provides an elegant, session-based interface that allows developers to quickly connect to MCP servers, test their functionality, and interact with them through a streaming conversation interface powered by Strands agents.

## Features

- 🚀 **Interactive CLI**: Elegant terminal interface with real-time streaming responses
- 🔧 **MCP Server Testing**: Connect to and test any MCP server implementation
- 💬 **Conversational Interface**: Powered by Strands agents for natural interactions
- ⚙️ **Configuration Management**: YAML-based server configuration with validation
- 🎨 **Rich UI**: Beautiful terminal output with syntax highlighting and formatting
- 🔄 **Session Management**: Context-aware conversations without file persistence

## Installation

### Prerequisites

- Python 3.10 or higher
- [UV package manager](https://docs.astral.sh/uv/getting-started/installation/) (recommended)

### Install from GitHub

```bash
# Using UV (recommended)
uv tool install git+https://github.com/nag763/eclaircp.git

# Using pip
pip install git+https://github.com/nag763/eclaircp.git
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/nag763/eclaircp.git
cd eclaircp

# Install with UV
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Run the tool
uv run eclaircp
```

## Quick Start

1. **Create a configuration file** (see [Configuration](#configuration) section below)
2. **Run EclairCP**:
   ```bash
   eclaircp --config config.yaml
   ```
3. **Select an MCP server** from your configuration
4. **Start chatting** with the connected MCP server through the elegant streaming interface

### Basic Usage

```bash
# Show help
eclaircp --help

# Use default configuration (looks for config.yaml in current directory)
eclaircp

# Specify a configuration file
eclaircp --config /path/to/your/config.yaml

# Interactive server selection
eclaircp --interactive
```

## Configuration

EclairCP uses YAML configuration files to manage MCP server connections. Create a `config.yaml` file in your working directory or specify a path with `--config`.

### Basic Configuration

```yaml
servers:
  aws-docs:
    command: "uvx"
    args: ["awslabs.aws-documentation-mcp-server@latest"]
    description: "AWS Documentation MCP Server"
    env:
      FASTMCP_LOG_LEVEL: "ERROR"
    timeout: 30
    retry_attempts: 3
  
  github:
    command: "uvx"
    args: ["github-mcp-server"]
    description: "GitHub MCP Server"
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
    timeout: 45
    retry_attempts: 2

default_session:
  server_name: "aws-docs"
  model: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  system_prompt: "You are a helpful assistant for testing MCP servers."
  max_context_length: 100000
```

### Configuration Options

#### Server Configuration
- `command`: The command to run the MCP server (e.g., "uvx", "python", "node")
- `args`: List of arguments to pass to the command
- `description`: Human-readable description of the server
- `env`: Environment variables to set when running the server
- `timeout`: Connection timeout in seconds (default: 30)
- `retry_attempts`: Number of connection retry attempts (default: 3)

#### Session Configuration
- `server_name`: Default server to connect to
- `model`: Strands agent model to use
- `system_prompt`: System prompt for the agent
- `max_context_length`: Maximum context length for conversations

### Example Configurations

#### Local MCP Server
```yaml
servers:
  local-server:
    command: "python"
    args: ["-m", "my_mcp_server"]
    description: "Local development MCP server"
    env:
      DEBUG: "true"
```

#### Docker-based MCP Server
```yaml
servers:
  docker-server:
    command: "docker"
    args: ["run", "--rm", "-i", "my-mcp-server:latest"]
    description: "Dockerized MCP server"
```

## Usage Examples

### Interactive Session

```bash
$ eclaircp
🚀 EclairCP - Elegant MCP Server Testing

Available servers:
1. aws-docs - AWS Documentation MCP Server
2. github - GitHub MCP Server

Select a server (1-2): 1

✅ Connected to aws-docs
🔧 Available tools: read_documentation, search_documentation, recommend

💬 Start your conversation (type 'exit' to quit):

> How do I create an S3 bucket?

🤖 I'll help you learn about creating S3 buckets. Let me search the AWS documentation...

[Tool: search_documentation]
Arguments: {"search_phrase": "create S3 bucket"}

📚 Based on the AWS documentation, here's how to create an S3 bucket...
```

### Batch Testing

```bash
# Test multiple servers quickly
eclaircp --test-all

# Test specific server
eclaircp --test aws-docs
```

## Troubleshooting

### Common Issues

#### "Command not found: uvx"
Install UV package manager:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### "Failed to connect to MCP server"
1. Check that the server command and arguments are correct
2. Verify environment variables are set (e.g., `GITHUB_TOKEN`)
3. Increase timeout in configuration
4. Check server logs for errors

#### "Configuration validation error"
- Ensure YAML syntax is correct
- Check that all required fields are present
- Validate environment variable references

### Debug Mode

Run with debug logging:
```bash
eclaircp --debug --config config.yaml
```

### Getting Help

- Use `eclaircp --help` for command-line options
- Type `help` during an interactive session for available commands
- Check the [examples](examples/) directory for sample configurations

## Development Status

🚧 **This project is currently under active development as part of a hackathon submission.**

The tool is being built with modern Python practices using:
- UV for dependency management
- Pydantic for data validation
- Rich and Textual for elegant TUI
- Strands Agents SDK for AI interactions
- Click for CLI framework

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

This project is part of a hackathon submission. Contributions and feedback are welcome!