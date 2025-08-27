---
inclusion: always
---

# EclairCP Technical Guidelines

## Required Technology Stack

### Core Dependencies
- **UV Package Manager**: Use `uv run` for all commands, `uv sync` for dependencies
- **Python 3.10+**: Target minimum version, support through 3.13
- **Pydantic v2**: All data models MUST use Pydantic for validation and serialization
- **Strands Agents SDK**: Handle AI conversations with streaming responses
- **MCP Client**: Model Context Protocol interactions (`mcp>=1.0.0`)
- **Rich/Textual**: Terminal UI components with syntax highlighting

### Code Quality Standards
- **Line Length**: 88 characters maximum
- **Formatter**: PyInk (Black-compatible) - use `uv run pyink`
- **Import Sorting**: isort with Black profile
- **Linting**: Pylint for code quality
- **Testing**: pytest with asyncio support and coverage reporting

## Architecture Requirements

### Async Programming
- Use `async/await` for all MCP client operations
- Implement streaming responses for real-time user feedback
- Handle asyncio event loops properly in CLI context

### Error Handling
- Use custom exception classes from `eclaircp.exceptions`
- Implement comprehensive error logging via `error_logging.py`
- Provide user-friendly error messages in terminal UI

### Configuration Management
- All config models MUST inherit from Pydantic BaseModel
- Use YAML for configuration files with proper validation
- Support environment variable overrides where appropriate

### Testing Patterns
- Write comprehensive tests for all modules
- Use pytest fixtures for common test setup
- Mock external dependencies (MCP servers, network calls)
- Maintain >90% test coverage

## Development Commands

```bash
# Setup and dependencies
uv sync                                    # Install all dependencies
uv run eclaircp                           # Run application locally

# Code quality
uv run pyink src/ tests/                  # Format code
uv run isort src/ tests/                  # Sort imports
uv run pylint src/eclaircp/               # Lint code

# Testing
uv run pytest                             # Run all tests
uv run pytest --cov=eclaircp --cov-report=html  # Coverage report
```

## Code Organization Rules

### Module Responsibilities
- `config.py`: Pydantic models, YAML parsing, validation only
- `mcp.py`: MCP protocol client management and tool proxying
- `session.py`: Conversation state and streaming response handling
- `ui.py`: Terminal display components using Rich/Textual
- `cli.py`: Command-line interface and application entry point

### Import Conventions
- Use absolute imports: `from eclaircp.config import ConfigModel`
- Group imports: stdlib, third-party, local
- Sort with isort Black profile

### Naming Conventions
- Classes: PascalCase (`ConfigManager`, `MCPClient`)
- Functions/variables: snake_case (`load_config`, `server_url`)
- Constants: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`)
- Files: snake_case (`error_logging.py`)

## Performance Guidelines
- Use async context managers for MCP connections
- Implement proper resource cleanup in finally blocks
- Stream responses to avoid memory buildup
- Cache configuration objects when appropriate