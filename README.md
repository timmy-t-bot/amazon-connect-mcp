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
- [Quick Start: Deploy Lambda Bridge](#quick-start-deploy-the-lambda-bridge)
- [Configuration](#configuration)
- [Tool Inventory](#tool-inventory)
- [Usage Examples](#usage-examples)
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

---

## Quick Start: Deploy the Lambda Bridge

The Lambda bridge is **optional but recommended** - it provides extended Connect APIs (phone number claiming, complex workflows, etc.). This uses **AWS CloudFormation** (AWS native) - no Terraform required.

### Prerequisites

1. **AWS CLI installed and configured**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, region (e.g., us-east-1)
   ```

2. **Verify AWS CLI version** (need 2.0+):
   ```bash
   aws --version
   ```

### Step 1: Clone the Repository

```bash
git clone https://github.com/timmy-t-bot/amazon-connect-mcp.git
cd amazon-connect-mcp
```

### Step 2: Deploy CloudFormation Stack

Use AWS CLI to create the CloudFormation stack:

```bash
aws cloudformation create-stack \
  --stack-name connect-api-bridge \
  --template-body file://cloudformation/lambda-bridge.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=Environment,ParameterValue=prod
```

This creates:
- Lambda function with IAM role
- API Gateway with 19 endpoints
- CloudWatch logs

⏱️ **Takes ~3-5 minutes**

### Step 3: Wait for Stack Creation

```bash
aws cloudformation wait stack-create-complete --stack-name connect-api-bridge
```

### Step 4: Get the API Gateway URL

After deployment succeeds, get the API URL from CloudFormation outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name connect-api-bridge \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

Copy this URL - you'll need it for the next step.

Example output:
```
https://abc123def.execute-api.us-east-1.amazonaws.com/prod
```

### Step 5: Configure the MCP Server

Set the environment variable:

```bash
export CONNECT_API_BRIDGE_URL="https://abc123def.execute-api.us-east-1.amazonaws.com/prod"
export CONNECT_API_BRIDGE_ENABLED="true"
```

Or add to your Hermes config (`~/.hermes/config.yaml`):

```yaml
mcp_servers:
  amazon_connect:
    command: "python"
    args: ["-m", "amazon_connect_mcp"]
    env:
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
      AWS_REGION: "us-east-1"
      CONNECT_API_BRIDGE_URL: "https://abc123def.execute-api.us-east-1.amazonaws.com/prod"
      CONNECT_API_BRIDGE_ENABLED: "true"
```

### Step 6: Test the Bridge

Verify it's working:

```bash
export API_URL=$(aws cloudformation describe-stacks \
  --stack-name connect-api-bridge \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text)

curl "$API_URL/health"
```

Expected output:
```json
{"status": "healthy", "version": "1.0.0"}
```

### Update the Stack (When Needed)

To update the CloudFormation stack after making changes:

```bash
aws cloudformation update-stack \
  --stack-name connect-api-bridge \
  --template-body file://cloudformation/lambda-bridge.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=Environment,ParameterValue=prod
```

### View Stack Events

To monitor stack creation progress:

```bash
aws cloudformation describe-stack-events \
  --stack-name connect-api-bridge \
  --query 'StackEvents[?ResourceStatus!=`CREATE_COMPLETE`].[LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
  --output table
```

### Cleanup (When Needed)

To delete all AWS resources created by CloudFormation:

```bash
aws cloudformation delete-stack --stack-name connect-api-bridge

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name connect-api-bridge
```

---

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

### Running the Server

**Stdio mode** (for MCP clients like Hermes):
```bash
python -m amazon_connect_mcp
```

Or on macOS:
```bash
python3 -m amazon_connect_mcp
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

### API Bridge Tools (19)

See [LAMBDA_BRIDGE_SPEC.md](docs/LAMBDA_BRIDGE_SPEC.md) for full documentation.

---

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

### Search for Phone Numbers (Requires Lambda Bridge)

```python
await mcp.call_tool("connect_phone_numbers_search", {
    "phone_number_country_code": "US",
    "phone_number_type": "TOLL_FREE",
    "max_results": 10
})
```

### Claim a Phone Number (Requires Lambda Bridge)

```python
await mcp.call_tool("connect_phone_numbers_claim", {
    "instance_id": "your-instance-id",
    "phone_number": "+1-800-555-0123",
    "description": "Main customer service line"
})
```

---

## Security Considerations

### AWS Credential Handling

- No AWS credentials are stored within the MCP server
- Credentials are obtained from standard AWS credential providers
- Environment variables or IAM roles are used for authentication

### Data Handling

- The MCP server does not persist Connect configuration data
- All API calls are executed in real-time against AWS APIs
- No sensitive data is logged (credentials redacted from logs)

### Lambda Bridge

- IAM role with minimal required permissions
- API Gateway can be configured with API keys or IAM auth
- No credentials stored in Lambda function code

---

## Troubleshooting

### Installation Issues

**macOS: uv refuses to install globally**
- Create and activate a virtual environment: `uv venv && source .venv/bin/activate`
- Then install: `uv pip install -e ".[dev]"`

**Python3 not found**
- On macOS, use `python3` instead of `python`
- Ensure Python 3.11+ is installed: `python3 --version`

### Runtime Issues

**"No Connect instance found"**
- Set `CONNECT_INSTANCE_ID` environment variable
- Or pass `instance_id` parameter to each tool call

**"Missing credentials"**
- Check AWS CLI is configured: `aws configure list`
- Verify environment variables are set
- For Lambda tools, ensure `CONNECT_API_BRIDGE_URL` is set

**"API Bridge not responding"**
- Verify the CloudFormation stack is created: `aws cloudformation describe-stacks --stack-name connect-api-bridge`
- Get the API URL:
  ```bash
  aws cloudformation describe-stacks \
    --stack-name connect-api-bridge \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text
  ```
- Ensure `CONNECT_API_BRIDGE_ENABLED=true`

**CloudFormation stack fails to create**
- Check events for detailed error: `aws cloudformation describe-stack-events --stack-name connect-api-bridge`
- Common causes:
  - Missing IAM permissions
  - Region not supported
  - Resource limits exceeded

---

## Development

```bash
# Clone the repository
git clone https://github.com/timmy-t-bot/amazon-connect-mcp.git
cd amazon-connect-mcp

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src
black src

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
│   │   └── templates/            # Contact flow templates
│   └── contact_flows/            # Contact flow tools
│       └── contact_flow_tools.py
├── lambda/                       # Lambda functions
├── cloudformation/               # CloudFormation templates
│   ├── lambda-bridge.yaml
│   └── README.md
├── terraform/                    # Terraform (optional, legacy)
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

---

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

---

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
