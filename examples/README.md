# EclairCP Examples

This directory contains example configuration files and usage scenarios for EclairCP.

## Configuration Files

### config.yaml

The main configuration file that defines MCP servers and session settings. Copy this file to your desired location and modify it according to your needs.

#### Basic Usage

1. Copy the example configuration:
   ```bash
   cp examples/config.yaml ~/.eclaircp/config.yaml
   ```

2. Edit the configuration to match your environment:
   - Set up environment variables (like GITHUB_TOKEN)
   - Modify server configurations as needed
   - Adjust timeout and retry settings

3. Run EclairCP with your configuration:
   ```bash
   eclaircp --config ~/.eclaircp/config.yaml
   ```

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