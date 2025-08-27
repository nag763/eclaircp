# Technology Stack & Build System

## Build System
- **Package Manager**: UV (modern Python package manager)
- **Build Backend**: Hatchling
- **Python Version**: >=3.10 (supports 3.10, 3.11, 3.12, 3.13)

## Core Dependencies
- **Strands Agents SDK**: AI conversation handling (`strands-agents>=0.1.0`)
- **MCP**: Model Context Protocol client (`mcp>=1.0.0`)
- **Pydantic**: Data validation and settings management (`pydantic>=2.0.0`)
- **PyYAML**: YAML configuration parsing (`pyyaml>=6.0`)
- **Rich**: Terminal formatting and display (`rich>=13.0.0`)
- **Textual**: Terminal UI framework (`textual>=0.40.0`)
- **Click**: CLI framework (`click>=8.0.0`)

## Development Tools
- **Code Formatting**: PyInk (Black-compatible formatter)
- **Linting**: Pylint
- **Import Sorting**: isort
- **Testing**: pytest with asyncio, mock, and coverage support

## Code Style Configuration
- **Line Length**: 88 characters
- **Import Style**: Black profile with trailing commas
- **Target Python**: 3.10+

## Common Commands

### Development Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
```

### Testing
```bash
# Run tests with coverage
uv run pytest

# Run tests with coverage report
uv run pytest --cov=eclaircp --cov-report=html
```

### Code Quality
```bash
# Format code
uv run pyink src/ tests/

# Sort imports
uv run isort src/ tests/

# Lint code
uv run pylint src/eclaircp/
```

### Running the Application
```bash
# Install and run locally
uv run eclaircp

# Or via entry point after installation
eclaircp
```

## Architecture Patterns
- **Pydantic Models**: All configuration and data structures use Pydantic for validation
- **Async/Await**: Asynchronous programming for MCP client interactions
- **Streaming**: Real-time response streaming for user interactions
- **Configuration-Driven**: YAML-based server and session configuration