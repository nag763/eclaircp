# EclairCP Examples

This directory contains example configuration files and usage scenarios for EclairCP.

## Configuration Files

This directory contains several example configurations for different use cases:

### config.yaml
The comprehensive configuration file with multiple MCP servers and detailed comments. Best for learning all available options.

### minimal-config.yaml
The simplest possible configuration with just one server. Perfect for getting started quickly.

### development-config.yaml
Optimized for development and testing with local servers, debug settings, and shorter timeouts.

### production-config.yaml
Production-ready configuration with enhanced error handling, longer timeouts, and security considerations.

Choose the configuration that best matches your use case and copy it to your desired location.

#### Basic Usage

1. **Quick Start**: Copy the minimal configuration:
   ```bash
   cp examples/minimal-config.yaml config.yaml
   eclaircp
   ```

2. **Full Setup**: Copy the comprehensive configuration:
   ```bash
   cp examples/config.yaml ~/.eclaircp/config.yaml
   ```

3. **Development**: Use the development configuration:
   ```bash
   cp examples/development-config.yaml dev-config.yaml
   eclaircp --config dev-config.yaml
   ```

4. **Production**: Use the production configuration:
   ```bash
   cp examples/production-config.yaml prod-config.yaml
   # Set required environment variables
   export GITHUB_TOKEN="your_token"
   export STRANDS_API_KEY="your_key"
   eclaircp --config prod-config.yaml
   ```

#### Configuration Selection Guide

- **New users**: Start with `minimal-config.yaml`
- **Developers**: Use `development-config.yaml` for local testing
- **Production use**: Use `production-config.yaml` with proper security
- **Learning**: Explore `config.yaml` for all available options

#### Server Configuration

Each server in the configuration requires:
- `command`: The executable command
- `args`: List of arguments to pass
- `description`: Human-readable description

Optional settings:
- `env`: Environment variables
- `timeout`: Connection timeout (default: 30 seconds)
- `retry_attempts`: Number of retries (default: 3)

#### Environment Variables

Some MCP servers require environment variables:
- GitHub server needs `GITHUB_TOKEN`
- Custom servers may need specific API keys or configuration

Set these in your shell or use a `.env` file:
```bash
export GITHUB_TOKEN="your_github_token_here"
```

## Common MCP Servers

### AWS Documentation Server
```yaml
aws-docs:
  command: "uvx"
  args: ["awslabs.aws-documentation-mcp-server@latest"]
  description: "AWS Documentation MCP Server"
  env:
    FASTMCP_LOG_LEVEL: "ERROR"
```

### GitHub Server
```yaml
github:
  command: "uvx"
  args: ["github-mcp-server"]
  description: "GitHub MCP Server"
  env:
    GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

### File System Server
```yaml
filesystem:
  command: "uvx"
  args: ["mcp-server-filesystem", "--base-path", "/safe/directory"]
  description: "File System MCP Server"
```

## Session Configuration

The `default_session` section configures the AI agent behavior:

```yaml
default_session:
  server_name: "aws-docs"  # Which server to connect to by default
  model: "us.anthropic.claude-3-7-sonnet-20250219-v1:0"  # AI model to use
  system_prompt: "Custom system prompt for the agent"
  max_context_length: 100000  # Maximum context window
```

## Troubleshooting

### Common Issues

1. **Server not found**: Ensure the MCP server package is installed
   ```bash
   uvx --help  # Check if uvx is installed
   ```

2. **Permission errors**: Check file permissions and directory access

3. **Environment variables**: Verify required environment variables are set
   ```bash
   echo $GITHUB_TOKEN  # Check if token is set
   ```

4. **Network issues**: Check firewall and network connectivity for remote servers

### Validation

Test your configuration file:
```bash
eclaircp --config your-config.yaml --validate
```

This will check the configuration syntax and validate server definitions without connecting.