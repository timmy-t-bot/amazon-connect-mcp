# Amazon Connect MCP Server

A Model Context Protocol (MCP) server for Amazon Connect outbound communication and infrastructure management.

## Overview

The Amazon Connect MCP Server provides AI agents with the ability to:

- **Manage Infrastructure**: Create and configure Amazon Connect instances, queues, hours of operation, and phone numbers
- **Handle Phone Numbers**: Search, claim, and manage phone numbers
- **Design Contact Flows**: Create outbound and inbound contact flows using parameterized templates
- **Control Campaigns**: Manage outbound communication campaigns
- **Process Cases**: Work with Amazon Connect Cases for customer issues

## Features

### Tool Categories

The server provides **100+ MCP tools** organized into categories:

| Category | Tools | Description |
|:---------|:------|:------------|
| **Contact Flows** | 12 | Create, update, delete, and manage contact flows with template support |
| **Phone Numbers** | 6 | Search, claim, release, and manage phone numbers |
| **Instances** | 5 | Create, describe, update, and delete Connect instances |
| **Queues** | 5 | Manage queues for call routing |
| **Hours of Operation** | 8 | Configure business hours and overrides |
| **Prompts** | 4 | Manage audio prompts and messages |
| **API Bridge** | 19 | Lambda-backed APIs for extended functionality |

### Key Capabilities

- **Templated Contact Flows**: Create sophisticated flows without writing JSON from scratch
- **Direct AWS Integration**: Uses boto3 for efficient API calls
- **Lambda Bridge**: Extended functionality for complex multi-step operations
- **SSML Support**: Rich text-to-speech with validation
- **Parameter Validation**: Built-in schema validation for all templates

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Tool Inventory](#tool-inventory)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Architecture](#architecture)

## Installation

### Prerequisites

- Python 3.11+
- AWS Account with appropriate permissions
- AWS CLI configured (optional but recommended)

### Using pip

```bash
pip install amazon-connect-mcp
```

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/timmy-t-bot/amazon-connect-mcp.git
cd amazon-connect-mcp
uv pip install -e ".[dev]"
```

#### macOS Troubleshooting

If you encounter errors on macOS (e.g., `uv pip install` refusing to install globally), follow these steps:

**1. Create and Activate the Virtual Environment**

Since you are using `uv`, we can let `uv` handle the virtual environment creation—it's much faster.

Create the environment:
```bash
uv venv
```

Now activate it so your terminal knows to use it:
```bash
source .venv/bin/activate
```

> 💡 You should see `(.venv)` appear at the beginning of your terminal prompt, indicating it's active.

**2. Install the Package**

Now that the virtual environment is active, run the install command again:
```bash
uv pip install -e ".[dev]"
```

**3. Run the MCP Server**

Once that finishes successfully, start the module. Because your Mac defaults to `python3`, use:
```bash
python3 -m amazon_connect_mcp
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|:---------|:---------|:------------|
| `AWS_REGION` | Yes | AWS region (e.g., `us-east-1`) |
| `AWS_PROFILE` | No* | AWS profile name |
| `AWS_ACCESS_KEY_ID` | No* | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | No* | AWS secret key |
| `CONNECT_INSTANCE_ID` | No | Default Connect instance ID |
| `CONNECT_INSTANCE_ALIAS` | No | Default instance alias |
| `CONNECT_API_BRIDGE_URL` | No | Lambda API Gateway URL |
| `CONNECT_API_BRIDGE_ENABLED` | No | Enable API bridge (`true`/`false`) |
| `CONNECT_API_BRIDGE_API_KEY` | No | API Gateway API key |
| `MCP_TRANSPORT` | No | Transport mode (`stdio` or `sse`) |
| `MCP_PORT` | No | Port for SSE mode (default: `8000`) |
| `TEMPLATES_DIR` | No | Custom templates directory path |

*Either `AWS_PROFILE` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` must be set.

### AWS Credentials

Configure AWS credentials using one of these methods:

1. **AWS CLI** (recommended):
   ```bash
   aws configure
   ```

2. **Environment variables**:
   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_REGION=us-east-1
   ```

3. **IAM role** (for AWS services):
   - Attach an IAM role to your EC2/ECS/Lambda resource

### IAM Permissions

The following permissions are required:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:Create*",
        "connect:Describe*",
        "connect:List*",
        "connect:Update*",
        "connect:Delete*",
        "connect:Search*",
        "connect:Claim*",
        "connect:Release*",
        "connect:Start*",
        "connect:Stop*",
        "connect-campaigns:*",
        "connectcases:*",
        "customer-profiles:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Quick Start

### Configure MCP Client

Add to your MCP client configuration (e.g., Claude Desktop, Hermes):

```json
{
  "mcpServers": {
    "amazon-connect": {
      "command": "python",
      "args": ["-m", "amazon_connect_mcp"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "default",
        "CONNECT_INSTANCE_ID": "your-instance-id",
        "CONNECT_API_BRIDGE_URL": "https://your-api-gateway.execute-api.region.amazonaws.com/prod"
      }
    }
  }
}
```

### Running the Server

**Stdio mode** (for MCP clients):
```bash
python -m amazon_connect_mcp
```

**Direct execution**:
```bash
python src/amazon_connect_mcp/server.py
```

### Verify Installation

```python
# Get server info
get_server_info()

# List contact flows
contact_flows_list(instance_id="your-instance-id")
```

## Usage Examples

### List Contact Flows

```python
await mcp.call_tool("contact_flows_list", {
    "instance_id": "your-instance-id",
    "max_results": 50
})
```

### Create Outbound Flow (Simple)

```python
await mcp.call_tool("contact_flows_create_outbound", {
    "instance_id": "your-instance-id",
    "name": "Appointment Reminder",
    "mode": "PLAY_PROMPT",
    "parameters": {
        "prompt_text": "Hello! This is a reminder of your appointment tomorrow at 2 PM.",
        "campaign_id": "appointment-campaign-001"
    }
})
```

### Create Outbound Flow (Interactive)

```python
await mcp.call_tool("contact_flows_create_outbound", {
    "instance_id": "your-instance-id",
    "name": "Smart Survey Flow",
    "mode": "AI_AGENT",
    "parameters": {
        "greeting_message": "Hello from our customer service team!",
        "confirmation_question": "Have you received your order?",
        "confirmation_reply": "Great! Thank you for confirming.",
        "lex_bot_arn": "arn:aws:lex:us-east-1:123456789:bot/survey-bot",
        "lambda_arn": "arn:aws:lambda:us-east-1:123456789:function:process-survey",
        "wait_timeout": 10
    }
})
```

### Search for Phone Numbers

```python
await mcp.call_tool("connect_phone_numbers_search", {
    "phone_number_country_code": "US",
    "phone_number_type": "TOLL_FREE",
    "max_results": 10
})
```

### Claim a Phone Number

```python
await mcp.call_tool("connect_phone_numbers_claim", {
    "instance_id": "your-instance-id",
    "phone_number": "+1-800-555-0123",
    "description": "Main customer service line"
})
```

## Tool Inventory

### Contact Flow Tools (12)

| Tool | Description |
|:-----|:------------|
| `contact_flows_list` | List all contact flows in an instance |
| `contact_flows_describe` | Get detailed contact flow information |
| `contact_flows_create` | Create a contact flow from raw JSON |
| `contact_flows_create_outbound` | Create templated outbound flow |
| `contact_flows_update_content` | Update flow content |
| `contact_flows_update_from_template` | Update flow using template |
| `contact_flows_delete` | Delete a contact flow |
| `contact_flows_list_templates` | List available templates |
| `contact_flows_get_template_schema` | Get template JSON schema |
| `contact_flows_validate_parameters` | Validate template parameters |
| `contact_flows_create_version` | Create flow version |
| `contact_flows_search` | Search flows with filters |

### Infrastructure Tools

#### Phone Numbers (6)
- `connect_phone_numbers_search`
- `connect_phone_numbers_claim`
- `connect_phone_numbers_release`
- `connect_phone_numbers_list`
- `connect_phone_numbers_describe`
- `connect_phone_numbers_update`

#### Instances (5)
- `connect_instances_list`
- `connect_instances_describe`
- `connect_instances_update`
- `connect_instances_create`
- `connect_instances_delete`

#### Queues (5)
- `connect_queues_list`
- `connect_queues_describe`
- `connect_queues_create`
- `connect_queues_update`
- `connect_queues_delete`

#### Hours of Operation (8)
- `connect_hours_of_operations_list`
- `connect_hours_of_operations_describe`
- `connect_hours_of_operations_create`
- `connect_hours_of_operations_update`
- `connect_hours_of_operations_delete`
- `connect_hours_of_operations_create_override`
- `connect_hours_of_operations_delete_override`
- `connect_hours_of_operations_describe_override`

#### Prompts (4)
- `connect_prompts_list`
- `connect_prompts_describe`
- `connect_prompts_create`
- `connect_prompts_delete`

## Security Considerations

### Data Protection

- **No credential storage**: AWS credentials are not stored by the MCP server
- **Environment isolation**: Each tool call operates within its own context
- **No logging of sensitive data**: API keys and tokens are not logged

### Access Control

- Follow principle of least privilege when creating IAM policies
- Use separate AWS profiles for different environments
- Enable CloudTrail logging for audit purposes

### Network Security

- When using API Bridge, ensure API Gateway uses TLS 1.2+
- Configure appropriate CORS settings for API Gateway
- Use VPC endpoints for AWS service access when possible

## Troubleshooting

### Common Issues

**Issue**: `AWS credentials not found`

**Solution**: Ensure AWS credentials are configured:
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1
```

**Issue**: `Template not found`

**Solution**: Set TEMPLATES_DIR environment variable:
```bash
export TEMPLATES_DIR=/path/to/templates
```

**Issue**: `API Bridge not configured`

**Solution**: For Lambda-backed features, set:
```bash
export CONNECT_API_BRIDGE_URL=https://your-api.execute-api.region.amazonaws.com/prod
export CONNECT_API_BRIDGE_ENABLED=true
```

### Debug Mode

Enable verbose logging:
```bash
export MCP_LOG_LEVEL=debug
python -m amazon_connect_mcp
```

### Checking Tool Availability

```python
# Get all available tools
await mcp.call_tool("get_server_info")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/timmy-t-bot/amazon-connect-mcp.git
cd amazon-connect-mcp

# Install with dev dependencies
uv pip install -e ".[dev,test]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Run type checking
mypy src
```

### Project Structure

```
amazon-connect-mcp/
├── src/
│   ├── amazon_connect_mcp/       # Main MCP server
│   │   ├── server.py             # FastMCP server entry point
│   │   ├── config.py             # Configuration management
│   │   ├── connect_api_bridge.py # Lambda bridge tools
│   │   ├── components/           # Infrastructure components
│   │   │   ├── hours_of_operation.py
│   │   │   ├── instance_manager.py
│   │   │   ├── phone_numbers.py
│   │   │   ├── prompts.py
│   │   │   ├── queues.py
│   │   │   └── integration.py
│   │   └── templates/            # Contact flow templates
│   │       ├── outbound/
│   │       ├── inbound/
│   │       ├── engine.py
│   │       └── registry.py
│   └── contact_flows/            # Contact flow tools
│       └── contact_flow_tools.py
├── lambda/                       # Lambda functions
│   ├── connect_api_handler.py
│   └── openapi.yaml
├── terraform/                    # Infrastructure as Code
├── tests/                        # Test suite
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md
│   ├── LAMBDA_BRIDGE_SPEC.md
│   ├── TOOL_MATRIX.md
│   ├── API_REFERENCE.md
│   └── HERMES_SETUP.md
└── examples/                     # Usage examples
    ├── basic_outbound_call.py
    ├── contact_flow_example.py
    ├── infrastructure_setup.py
    └── lambda_deployment.md
```

## API Bridge Setup

For APIs requiring the Lambda bridge:

```bash
cd terraform
terraform init
terraform apply -var="aws_region=us-east-1"
```

See [terraform/README.md](terraform/README.md) and [lambda_deployment.md](examples/lambda_deployment.md) for detailed setup instructions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP CLIENT (Hermes/Claude)                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ STDIO/SSE
┌──────────────────────────────▼──────────────────────────────────┐
│                  AMAZON CONNECT MCP SERVER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Contact Flow │  │  Components  │  │ API Bridge   │         │
│  │   Tools      │  │   (boto3)    │  │ (Lambda)     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼─────────────────┼────────────────┼────────────────────┘
          │                 │                │
          ▼                 ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Connect  │    │  Direct  │    │  Lambda  │
    │  APIs    │    │  boto3   │    │  Proxy   │
    └──────────┘    └──────────┘    └──────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by the [community Amazon Connect MCP server](https://github.com/mundurragacl/amazon-connect-mcp)

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/timmy-t-bot/amazon-connect-mcp/issues) page.

For discussions and questions, use [GitHub Discussions](https://github.com/timmy-t-bot/amazon-connect-mcp/discussions).
