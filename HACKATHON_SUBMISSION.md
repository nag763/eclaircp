# EclairCP - Hackathon Submission

## Project Overview

**EclairCP** is an elegant CLI tool for testing and interacting with Model Context Protocol (MCP) servers. Built with modern Python practices and powered by Strands agents, it provides developers with a streamlined interface to connect to MCP servers, test their functionality, and interact with them through streaming conversations.

## 🎯 Problem Statement

Developers working with MCP servers face several challenges:
- **Complex Setup**: Difficult to quickly test MCP server implementations
- **Poor UX**: Existing tools lack elegant user interfaces
- **Limited Interaction**: No conversational interface for natural testing
- **Error Handling**: Poor error messages and recovery mechanisms
- **Configuration Management**: No standardized way to manage multiple server configurations

## 💡 Solution

EclairCP addresses these challenges by providing:

### 🚀 **Elegant CLI Interface**
- Beautiful terminal UI with Rich and Textual
- Real-time streaming responses
- Interactive server selection
- Comprehensive help system

### 🔧 **MCP Server Testing**
- Connect to any MCP server implementation
- Test tool functionality and edge cases
- Validate server responses and behavior
- Debug issues with detailed error messages

### 💬 **Conversational Interface**
- Powered by Strands agents for natural interactions
- Context-aware conversations
- Streaming responses for real-time feedback
- Session management without file persistence

### ⚙️ **Configuration Management**
- YAML-based server configuration with Pydantic validation
- Support for multiple server environments
- Environment variable handling
- Flexible timeout and retry settings

## 🛠 Technical Implementation

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │────│ Session Manager  │────│  Strands Agent  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────│ Config Manager   │             │
                        └──────────────────┘             │
                                 │                       │
                        ┌──────────────────┐    ┌─────────────────┐
                        │   MCP Client     │────│   MCP Server    │
                        └──────────────────┘    └─────────────────┘
                                 │
                        ┌──────────────────┐
                        │  UI Components   │
                        └──────────────────┘
```

### Technology Stack
- **Language**: Python 3.10+
- **Package Manager**: UV (modern Python package manager)
- **AI Framework**: Strands Agents SDK
- **MCP Integration**: MCP client library
- **Data Validation**: Pydantic v2
- **CLI Framework**: Click
- **Terminal UI**: Rich + Textual
- **Configuration**: PyYAML
- **Testing**: pytest with 88% coverage

### Key Features Implemented

#### 1. **Pydantic-Based Configuration System**
```python
class MCPServerConfig(BaseModel):
    name: str
    command: str
    args: List[str]
    description: str = ""
    env: Dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)
```

#### 2. **Streaming Response Handler**
```python
class StreamingHandler:
    def handle_stream_event(self, event: Dict) -> None:
        """Process streaming events from Strands agent"""
        # Real-time response processing with event streaming
```

#### 3. **MCP Tool Proxy**
```python
class MCPToolProxy:
    def get_strands_tools(self) -> List[Callable]:
        """Convert MCP tools to Strands-compatible tools"""
        # Seamless integration between MCP and Strands
```

#### 4. **Elegant Error Handling**
```python
class EclairCPError(Exception):
    """Base exception with user-friendly messages"""
    
class ConfigurationError(EclairCPError):
    """Configuration-related errors with suggestions"""
```

## 🎨 User Experience

### Installation
```bash
# Using UV (recommended)
uv tool install git+https://github.com/nag763/eclaircp.git

# Using pip
pip install git+https://github.com/nag763/eclaircp.git
```

### Configuration
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

default_session:
  server_name: "aws-docs"
  model: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  system_prompt: "You are a helpful assistant for testing MCP servers."
```

### Usage
```bash
# Start with default configuration
eclaircp

# Use specific configuration
eclaircp --config my-config.yaml

# Interactive server selection
eclaircp --interactive
```

### Example Interaction
```
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

## 🧪 Testing & Quality

### Test Coverage
- **290 tests** with **88% coverage**
- Unit tests for all core components
- Integration tests with mock and real MCP servers
- End-to-end workflow testing
- Performance and error scenario testing

### Code Quality
- **PyInk** formatting (Black-compatible)
- **Pylint** linting with custom configuration
- **isort** import sorting
- **Type hints** throughout codebase
- **Pydantic validation** for all data structures

### Development Tools
```bash
# Run tests with coverage
uv run pytest --cov=eclaircp --cov-report=html

# Format code
uv run pyink src/ tests/

# Lint code
uv run pylint src/eclaircp/
```

## 🏗 Kiro Usage & Development Process

### Kiro Integration
This project was developed using **Kiro**, an AI-powered IDE, which significantly enhanced the development process:

#### 1. **Spec-Driven Development**
- Used Kiro's spec workflow to transform the initial idea into detailed requirements
- Created comprehensive design documents with architecture diagrams
- Generated actionable implementation tasks with clear dependencies

#### 2. **AI-Assisted Implementation**
- Leveraged Kiro's code generation capabilities for boilerplate and complex logic
- Used AI suggestions for error handling patterns and best practices
- Automated test generation for comprehensive coverage

#### 3. **Iterative Refinement**
- Kiro's feedback loops helped refine requirements and design decisions
- Real-time code analysis and suggestions improved code quality
- Automated documentation generation and updates

#### 4. **Quality Assurance**
- Kiro's integrated testing tools ensured high test coverage
- Code formatting and linting automation maintained consistency
- Performance analysis and optimization suggestions

### Development Workflow with Kiro
```
Idea → Requirements (Kiro Spec) → Design → Implementation Tasks → Code Generation → Testing → Refinement
```

This workflow enabled rapid development while maintaining high code quality and comprehensive documentation.

## 📊 Project Metrics

### Development Stats
- **Lines of Code**: ~1,500 (source code)
- **Test Coverage**: 88%
- **Dependencies**: 8 core, 7 development
- **Development Time**: Hackathon duration
- **Git Commits**: 50+ with clear history

### Features Delivered
- ✅ CLI interface with argument parsing
- ✅ YAML configuration management with validation
- ✅ MCP server connection and tool integration
- ✅ Strands agent-powered conversations
- ✅ Streaming response interface
- ✅ Interactive server selection
- ✅ Comprehensive error handling
- ✅ Rich terminal UI components
- ✅ Session management
- ✅ Example configurations and documentation

## 🚀 Future Enhancements

### Planned Features
1. **Plugin System**: Support for custom MCP server plugins
2. **Configuration UI**: Web-based configuration management
3. **Batch Testing**: Automated testing of multiple servers
4. **Performance Monitoring**: Real-time performance metrics
5. **Docker Support**: Containerized deployment options

### Scalability Considerations
- **Async Architecture**: Built for concurrent server connections
- **Modular Design**: Easy to extend with new features
- **Configuration-Driven**: Supports unlimited server configurations
- **Cloud-Ready**: Designed for deployment in various environments

## 🏆 Hackathon Achievements

### Innovation
- **First-of-its-kind**: Elegant CLI tool specifically for MCP server testing
- **AI Integration**: Novel use of Strands agents for conversational MCP interaction
- **Developer Experience**: Focus on UX that makes MCP testing enjoyable

### Technical Excellence
- **Modern Python**: Leverages latest Python features and best practices
- **High Test Coverage**: 88% coverage with comprehensive test suite
- **Production Ready**: Proper packaging, documentation, and error handling
- **Open Source**: MIT licensed for community contribution

### Impact
- **Developer Productivity**: Significantly reduces time to test MCP servers
- **Learning Tool**: Helps developers understand MCP protocol through interaction
- **Community Resource**: Provides examples and patterns for MCP development

## 📝 Conclusion

EclairCP represents a significant advancement in MCP server development tooling. By combining elegant user experience with powerful AI-driven interactions, it addresses real pain points faced by developers working with the Model Context Protocol.

The project demonstrates:
- **Technical Proficiency**: Modern Python development with comprehensive testing
- **User-Centric Design**: Focus on developer experience and usability
- **Innovation**: Novel approach to MCP server testing and validation
- **Quality**: Production-ready code with proper documentation and packaging

Built with Kiro's assistance, this project showcases how AI-powered development tools can accelerate innovation while maintaining high quality standards.

---

## 📚 Resources

- **Repository**: https://github.com/nag763/eclaircp
- **Documentation**: See README.md and examples/
- **Demo**: Run `python demo.py` for interactive demonstration
- **License**: MIT License

**Thank you for considering EclairCP for the hackathon!** 🎉