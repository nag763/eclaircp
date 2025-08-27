# Project Structure & Organization

## Root Directory Layout
```
eclaircp/
├── src/eclaircp/          # Main source code
├── tests/                 # Test files
├── examples/              # Example configurations
├── htmlcov/              # Coverage reports (generated)
├── pyproject.toml        # Project configuration
├── uv.lock              # Dependency lock file
├── README.md            # Project documentation
└── LICENSE              # MIT license
```

## Source Code Organization (`src/eclaircp/`)
- `__init__.py` - Package initialization and public API exports
- `cli.py` - Main CLI entry point and command handling
- `config.py` - Configuration management (Pydantic models, YAML parsing)
- `mcp.py` - MCP client management and tool proxying
- `session.py` - Session management and streaming handlers
- `ui.py` - Terminal UI components (Rich/Textual)

## Test Structure (`tests/`)
- Mirror the source structure with `test_*.py` files
- Each module has corresponding test file (e.g., `test_config.py` for `config.py`)
- Tests use pytest with asyncio, mock, and coverage support

## Configuration Examples (`examples/`)
- `config.yaml` - Comprehensive example configuration
- `README.md` - Configuration documentation and examples

## Key Conventions

### Module Responsibilities
- **config.py**: All Pydantic models, YAML handling, validation logic
- **mcp.py**: MCP protocol client management, tool discovery and execution
- **session.py**: Conversation state, streaming response handling
- **ui.py**: Terminal display, user interaction components
- **cli.py**: Command-line interface, argument parsing, main entry point

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports from package root (`from eclaircp.config import ...`)

### File Naming
- Snake_case for all Python files
- Test files prefixed with `test_`
- Configuration files use `.yaml` extension
- Documentation files use `.md` extension

### Code Organization Patterns
- Pydantic models defined at module level
- Exception classes defined near related functionality
- Manager classes handle complex operations (ConfigManager, MCPClientManager)
- Separate concerns: validation, business logic, UI, and protocol handling