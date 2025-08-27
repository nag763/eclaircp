# Changelog

All notable changes to EclairCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-27

### 🎉 Initial Release

This is the first release of EclairCP, an elegant CLI tool for testing and interacting with Model Context Protocol (MCP) servers.

### ✨ Features

- **Interactive CLI Interface**: Beautiful terminal interface with real-time streaming responses
- **MCP Server Testing**: Connect to and validate any MCP server implementation
- **Conversational Interface**: Powered by Strands agents for natural AI interactions
- **YAML Configuration**: Flexible server configuration with Pydantic validation
- **Rich Terminal UI**: Syntax highlighting, formatting, and elegant output using Rich/Textual
- **Session Management**: Context-aware conversations with streaming support
- **Multiple Server Support**: Configure and switch between different MCP servers
- **Environment Integration**: Support for environment variables and custom commands

### 🔧 Technical Highlights

- **Modern Python Stack**: Built with Python 3.10+ using UV package manager
- **Async Architecture**: Full async/await support for MCP protocol operations
- **Comprehensive Testing**: >90% test coverage with pytest, including integration tests
- **Code Quality**: Formatted with PyInk, linted with Pylint, imports sorted with isort
- **Type Safety**: Full Pydantic v2 integration for data validation and serialization

### 📦 Dependencies

- **Core**: Strands Agents SDK, MCP Client (>=1.0.0), Pydantic v2
- **UI**: Rich (>=13.0.0), Textual (>=0.40.0), Click (>=8.0.0)
- **Config**: PyYAML (>=6.0) for configuration management

### 🚀 Installation

```bash
# Using UV (recommended)
uv tool install git+https://github.com/nag763/eclaircp.git

# Using pip
pip install git+https://github.com/nag763/eclaircp.git
```

### 📖 Usage

```bash
# Basic usage with default config
eclaircp

# Specify configuration file
eclaircp --config config.yaml

# Interactive server selection
eclaircp --interactive
```

### 🎯 Supported MCP Servers

- AWS Documentation MCP Server
- GitHub MCP Server  
- Custom local and Docker-based servers
- Any MCP-compliant server implementation

### 🏗️ Architecture

- **config.py**: Pydantic models and YAML configuration management
- **mcp.py**: MCP protocol client and tool proxying
- **session.py**: Conversation state and streaming response handling
- **ui.py**: Terminal UI components with Rich/Textual
- **cli.py**: Command-line interface and application entry point

### 🧪 Development Status

This release represents a fully functional hackathon submission with:
- Complete feature implementation
- Comprehensive test suite
- Production-ready code quality
- Extensive documentation and examples

### 🔮 Future Plans

- Enhanced error handling and recovery
- Plugin system for custom MCP integrations
- Configuration UI and management tools
- Performance optimizations and caching
- Extended server compatibility testing

---

**Note**: This is a hackathon project showcasing modern Python development practices and elegant CLI design for MCP server testing.