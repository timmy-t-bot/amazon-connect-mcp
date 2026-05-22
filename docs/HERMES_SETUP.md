# Hermes Setup Guide

This guide explains how to configure the Amazon Connect MCP Server with Hermes Agent.

## Overview

Hermes supports MCP servers via configuration files. The Amazon Connect MCP Server can be added to Hermes' configuration to enable contact center management capabilities.

## Prerequisites

- Hermes Agent installed and running
- Amazon Connect MCP Server installed (`pip install amazon-connect-mcp`)
- AWS credentials configured
- Amazon Connect instance ID (optional but recommended)

## Configuration Methods

### Method 1: Direct Configuration (Recommended)

Add the MCP server directly to your Hermes configuration file.

**Linux/macOS**:
```yaml
# ~/.config/hermes-agent/config.yaml
# or
# ~/hermes/config.yaml
```

**Windows**:
```yaml
# %APPDATA%\hermes-agent\config.yaml
# or
# C:\Users\<username>\hermes\config.yaml
```

### Method 2: Environment-Based Configuration

Create a dedicated configuration file and reference it via environment variable:

```bash
export HERMES_CONFIG=/path/to/connect-mcp-config.yaml
```

## Configuration Snippet

Add to your Hermes configuration:

```yaml
mcpServers:
  amazon-connect:
    command: python
    args:
      - "-m"
      - "amazon_connect_mcp"
    env:
      AWS_REGION: "us-east-1"
      AWS_PROFILE: "default"
      CONNECT_INSTANCE_ID: "your-instance-id-here"
      CONNECT_API_BRIDGE_URL: ""
      CONNECT_API_BRIDGE_ENABLED: "false"
      MCP_TRANSPORT: "stdio"
```

### Full Example Configuration

```yaml
# Hermes Configuration File
# Location: ~/.config/hermes-agent/config.yaml

# Main settings
name: "hermes-agent"
version: "1.0"

# MCP Servers
mcpServers:
  # Amazon Connect MCP Server
  amazon-connect:
    name: "Amazon Connect MCP"
    description: "Manage Amazon Connect contact center infrastructure"
    command: python
    args:
      - "-m"
      - "amazon_connect_mcp"
    workingDirectory: null
    timeout: 60
    env:
      # AWS Configuration
      AWS_REGION: "us-east-1"
      AWS_PROFILE: "default"
      # AWS_ACCESS_KEY_ID: ""        # Optional: Use for explicit credentials
      # AWS_SECRET_ACCESS_KEY: ""  # Optional: Use for explicit credentials
      
      # Amazon Connect Configuration
      CONNECT_INSTANCE_ID: "12345678-1234-1234-1234-123456789012"
      CONNECT_INSTANCE_ALIAS: "my-contact-center"
      
      # API Bridge Configuration (optional)
      # CONNECT_API_BRIDGE_URL: "https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"
      # CONNECT_API_BRIDGE_ENABLED: "true"
      # CONNECT_API_BRIDGE_API_KEY: "your-api-key-here"
      
      # MCP Server Configuration
      MCP_TRANSPORT: "stdio"
      
      # Template Directory (optional)
      # TEMPLATES_DIR: "/path/to/custom/templates"
      
    # Tool filtering (optional)
    toolFilter:
      include:
        - "^contact_flows_"      # Include all contact flow tools
        - "connect_"             # Include all connect tools
      exclude:
        - ".*_delete$"           # Exclude deletion tools
        - ".*_release$"        # Exclude release tools

# Additional MCP servers
mcpServers:
  amazon-connect:
    command: python
    args:
      - "-m"
      - "amazon_connect_mcp"
    env:
      AWS_REGION: "us-east-1"
      AWS_PROFILE: "default"
      CONNECT_INSTANCE_ID: "your-instance-id"
```

## Environment Variables Reference

### Required

| Variable | Description | Example |
|:---------|:------------|:--------|
| `AWS_REGION` | AWS Region | `us-east-1` |

### AWS Credentials (Choose One)

| Variable | Description | Example |
|:---------|:------------|:--------|
| `AWS_PROFILE` | AWS CLI profile name | `default` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Explicit credentials | `AKIA...` |

### Amazon Connect Settings

| Variable | Required | Description | Example |
|:---------|:---------|:------------|:--------|
| `CONNECT_INSTANCE_ID` | No | Default instance ID | `12345678-...` |
| `CONNECT_INSTANCE_ALIAS` | No | Instance alias | `my-contact-center` |

### API Bridge (Optional)

| Variable | Required | Description | Example |
|:---------|:---------|:------------|:--------|
| `CONNECT_API_BRIDGE_URL` | No* | API Gateway URL | `https://xxxxx.execute-api...` |
| `CONNECT_API_BRIDGE_ENABLED` | No | Enable bridge | `true` |
| `CONNECT_API_BRIDGE_API_KEY` | No | API key for auth | `your-api-key` |

*Required when using Lambda-backed tools

### MCP Server Settings

| Variable | Required | Description | Default |
|:---------|:---------|:------------|:--------|
| `MCP_TRANSPORT` | No | Transport mode | `stdio` |
| `MCP_PORT` | No | Port for SSE mode | `8000` |

## Configuration Examples

### Minimal Configuration

```yaml
mcpServers:
  amazon-connect:
    command: python
    args: ["-m", "amazon_connect_mcp"]
    env:
      AWS_REGION: "us-east-1"
      AWS_PROFILE: "default"
```

### Full Configuration with API Bridge

```yaml
mcpServers:
  amazon-connect:
    command: python
    args: ["-m", "amazon_connect_mcp"]
    env:
      # AWS
      AWS_REGION: "us-east-1"
      AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"
      AWS_SECRET_ACCESS_KEY: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
      
      # Connect
      CONNECT_INSTANCE_ID: "12345678-1234-1234-1234-123456789012"
      CONNECT_INSTANCE_ALIAS: "production-cc"
      
      # API Bridge
      CONNECT_API_BRIDGE_URL: "https://abc123def.execute-api.us-east-1.amazonaws.com/prod"
      CONNECT_API_BRIDGE_ENABLED: "true"
      CONNECT_API_BRIDGE_API_KEY: "my-api-key-123"
      
      # Server
      MCP_TRANSPORT: "stdio"
```

### Multi-Region Configuration

For managing multiple regions, add separate configs:

```yaml
mcpServers:
  amazon-connect-us-east:
    command: python
    args: ["-m", "amazon_connect_mcp"]
    env:
      AWS_REGION: "us-east-1"
      CONNECT_INSTANCE_ID: "us-east-instance-id"
      
  amazon-connect-us-west:
    command: python
    args: ["-m", "amazon_connect_mcp"]
    env:
      AWS_REGION: "us-west-2"
      CONNECT_INSTANCE_ID: "us-west-instance-id"
```

## AWS Credentials Setup

### Option 1: AWS CLI Profile (Recommended)

1. Configure AWS CLI:
   ```bash
   aws configure
   # Enter Access Key ID
   # Enter Secret Access Key
   # Enter Default region (e.g., us-east-1)
   # Enter Default output format (json)
   ```

2. Reference profile in config:
   ```yaml
   env:
     AWS_PROFILE: "default"
   ```

### Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

In Hermes config:
```yaml
env:
  AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
  AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
```

### Option 3: Credentials File

Use `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[production]
aws_access_key_id = AKIAI44QH8DHBEXAMPLE
aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
```

Reference in config:
```yaml
mcpServers:
  amazon-connect-dev:
    env:
      AWS_PROFILE: "default"
  amazon-connect-prod:
    env:
      AWS_PROFILE: "production"
```

## Tool Filtering

Limit which tools are available to Hermes:

```yaml
mcpServers:
  amazon-connect:
    command: python
    args: ["-m", "amazon_connect_mcp"]
    # Filter read-only operations only
    toolFilter:
      include:
        - "contact_flows_list$"
        - "contact_flows_describe$"
        - "contact_flows_get_template_schema$"
        - "contact_flows_validate_parameters$"
        - "connect_instances_list$"
        - "connect_instances_describe$"
        - "connect_phone_numbers_list$"
        - "connect_queues_list$"
      exclude:
        - ".*"  # Exclude everything else
```

## Testing Your Configuration

### 1. Validate Configuration

```bash
# Check Hermes can load the config
hermes-agent --validate-config
```

### 2. Test Server Connection

Start Hermes and run:

```
List my Amazon Connect contact flows for instance 12345678-...
```

Or directly test the MCP server:

```bash
python -m amazon_connect_mcp
```

### 3. Verify Tool Availability

In Hermes, check available tools:

```
What Amazon Connect tools are available?
```

## Troubleshooting

### Server Not Found

**Symptom**: Hermes reports "MCP server not found"

**Solutions**:
1. Verify Python path:
   ```bash
   which python
   which python3
   ```

2. Check installation:
   ```bash
   pip show amazon-connect-mcp
   ```

3. Try full path:
   ```yaml
   command: /usr/bin/python3
   args:
     - "-m"
     - "amazon_connect_mcp"
   ```

### AWS Credentials Error

**Symptom**: "AWS credentials not found"

**Solutions**:
1. Verify AWS CLI:
   ```bash
   aws sts get-caller-identity
   ```

2. Check profile exists:
   ```bash
   aws configure list-profiles
   ```

3. Use explicit credentials in config

### Instance Not Found

**Symptom**: "Instance not found" errors

**Solutions**:
1. Verify instance exists:
   ```bash
   aws connect list-instances
   ```

2. Check region matches:
   ```bash
   aws connect describe-instance --instance-id your-id
   ```

3. Verify IAM permissions

### Tool Calls Failing

**Symptom**: Tools return errors

**Check**:
1. Run server directly:
   ```bash
   python -m amazon_connect_mcp
   ```

2. Check logs:
   ```bash
   cat ~/.local/share/hermes-agent/logs/*.log
   ```

3. Verify environment variables:
   ```bash
   echo $AWS_REGION
   echo $CONNECT_INSTANCE_ID
   ```

## Best Practices

### 1. Use Instance Aliases

```yaml
mcpServers:
  amazon-connect-production:
    env:
      CONNECT_INSTANCE_ALIAS: "prod-contact-center"
  amazon-connect-staging:
    env:
      CONNECT_INSTANCE_ALIAS: "staging-contact-center"
```

### 2. Separate Read/Write Access

```yaml
# Read-only config
mcpServers:
  connect-read-only:
    env:
      AWS_ACCESS_KEY_ID: "${CONNECT_READ_ACCESS_KEY}"
      AWS_SECRET_ACCESS_KEY: "${CONNECT_READ_SECRET}"
    toolFilter:
      include:
        - "^contact_flows_list"
        - "^connect_.*_list"
        - "^connect_.*_describe"
```

### 3. Use Environment Variables for Secrets

Never commit credentials to version control:

```yaml
# config.yaml
env:
  AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
  AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
```

```bash
# .env file (gitignored)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXU...
```

### 4. Enable API Bridge for Production

For production use, deploy Lambda bridge:

```yaml
env:
  CONNECT_API_BRIDGE_ENABLED: "true"
  CONNECT_API_BRIDGE_URL: "https://...execute-api...amazonaws.com/prod"
```

### 5. Set Appropriate Timeouts

Complex operations may take time:

```yaml
mcpServers:
  amazon-connect:
    timeout: 120  # 2 minutes
```

## Validation Checklist

Before deploying to production:

- [ ] AWS credentials configured
- [ ] Instance ID verified
- [ ] Required IAM permissions granted
- [ ] API Bridge deployed (if using)
- [ ] Tools tested individually
- [ ] Error scenarios tested
- [ ] Timeout values appropriate
- [ ] Secrets not in version control

## Getting Help

### Resources

- [Amazon Connect MCP Documentation](https://github.com/nousresearch/amazon-connect-mcp)
- [AWS Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [Hermes Documentation](https://hermes-agent.nousresearch.com/docs)

### Debugging

Enable debug logging:

```yaml
mcpServers:
  amazon-connect:
    env:
      MCP_LOG_LEVEL: "debug"
```

Check server info:

```python
# In Hermes
get_server_info()
```

## Example Workflows

### Example 1: Create Contact Flow

```
User: Create an outbound contact flow named "Welcome Call" that plays a greeting message

Hermes: I'll create an outbound contact flow for you.

[Uses contact_flows_create_outbound with mode=PLAY_PROMPT]
```

### Example 2: Manage Phone Numbers

```
User: Search for available toll-free numbers in the US and claim one

Hermes: I'll search for and claim a US toll-free number.

[Uses connect_phone_numbers_search then connect_phone_numbers_claim]
```

### Example 3: Set Up Queue

```
User: Create a new customer support queue with business hours

Hermes: I'll set up a customer support queue with business hours.

[Uses connect_hours_of_operations_create then connect_queues_create]
```

## Next Steps

1. Review [API_REFERENCE.md](API_REFERENCE.md) for detailed tool documentation
2. Check [examples/](../examples/) for code samples
3. See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
4. Read [lambda_deployment.md](../examples/lambda_deployment.md) for API Bridge setup
