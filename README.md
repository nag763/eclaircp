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

## Quick Start

*Installation and usage instructions will be added as the project develops.*

## Configuration

EclairCP uses YAML configuration files to manage MCP server connections:

```yaml
servers:
  aws-docs:
    command: "uvx"
    args: ["awslabs.aws-documentation-mcp-server@latest"]
    description: "AWS Documentation MCP Server"
    env:
      FASTMCP_LOG_LEVEL: "ERROR"
  
  github:
    command: "uvx"
    args: ["github-mcp-server"]
    description: "GitHub MCP Server"
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

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