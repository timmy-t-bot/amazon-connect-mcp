# Amazon Connect MCP Server

Enable AI agents to make outbound calls via Amazon Connect.

## Quick Start (1-liner)

```bash
git clone https://github.com/timmy-t-bot/amazon-connect-mcp.git
cd amazon-connect-mcp
./deploy.sh
```

This creates everything:
- Amazon Connect instance
- Phone number (claimed automatically)
- Default queue
- Outbound contact flow
- Lambda + API Gateway bridge
- IAM role with all permissions

## What You Get

An MCP server with **48+ tools** for AI agents to manage Amazon Connect:
- **Start outbound calls** with dynamic messages (`connect_start_outbound_voice_contact`)
- **Manage instances**, queues, phone numbers, hours of operation
- **Create contact flows** from templates
- **Claim/search phone numbers**
- **Full AWS API coverage** via direct boto3

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   AI AGENT (Hermes/Claude)                  │
│         calls MCP tool: connect_start_outbound_voice_contact │
│              with attributes={"message": "Your appointment..."} │
└──────────────────────────────┬─────────────────────────────┘
                               │ MCP stdio
┌──────────────────────────────▼─────────────────────────────┐
│            AMAZON CONNECT MCP SERVER (Python + FastMCP)    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 48+ Tools    │  │ Templates    │  │ API Bridge   │     │
│  │ (direct)     │  │ (JSON + {{}})│  │ (Lambda)     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                         │ boto3                               │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              AWS CLOUDFORMATION SINGLE STACK                 │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│   │ Connect  │  │ Phone  │  │ Default  │  │ Contact  │ │
│   │ Instance │  │ Number │  │ Queue    │  │ Flow     │ │
│   └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬─────┘ │
│        │             │           │             │         │
│   ┌────┴─────────────┴───────────┴─────────────┴─────┐ │
│   │              Lambda + API Gateway                    │ │
│   └──────────────────────────────────────────────────────┘ │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│   │ IAM Role    │  │ CloudWatch  │  │ Stack Outputs   │  │
│   │ (minimal)   │  │ (14 days)   │  │ (API URL, IDs)  │  │
│   └─────────────┘  └─────────────┘  └─────────────────┘  │
└────────────────────────────────────────────────────────────┘
                          │
                     📞 Outbound call
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    CUSTOMER PHONE                            │
│  • Hears TTS message from $.Attributes.message               │
│  • Presses 1 (confirm) or 2 (decline) if interactive          │
│  • Call ends, disposition stored in Connect                 │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

**1. Deploy** (one command):
```
./deploy.sh → CloudFormation creates everything → Auto-claims phone number → Outputs ready MCP config
```

**2. Place Outbound Call** (AI agent):
```
AI Agent calls MCP tool → boto3 → connect:StartOutboundVoiceContact → AWS dials customer → Contact flow runs → TTS plays message
```

**3. Manage Infrastructure** (AI agent):
```
AI Agent queries → list_instances, list_queues, list_phone_numbers, search_available_numbers, claim_phone_number, create_contact_flow
```

### Tool Count: 48+

| Category | Count | Key Tool |
|----------|-------|----------|
| **Outbound** | 4 | `connect_start_outbound_voice_contact` (with Attributes dict) |
| **Instances** | 5 | create, describe, list, update, delete |
| **Phone Numbers** | 6 | search, claim, release, list, describe, update |
| **Queues** | 6 | CRUD + update name |
| **Hours of Operation** | 8 | CRUD + overrides |
| **Prompts** | 4 | CRUD |
| **Contact Flows** | 12 | template-driven create/update + raw JSON |
| **Routing Profiles** | 2 | list, describe |
| **Users** | 2 | list, describe |

### Cost (Light Usage)

| Component | Monthly |
|-----------|---------|
| Connect instance | Free |
| Phone number | ~$2 |
| Outbound minutes | ~$0.018/min |
| Lambda + API GW | ~$4 |
| **Total** | **~$25/mo** |

## Prerequisites

- AWS CLI configured (`aws configure`)
- Python 3.9+
- `ollama login` (if using Ollama Cloud)

## MCP Client Config

### Hermes Agent

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  amazon-connect:
    command: "python"
    args: ["-m", "amazon_connect_mcp.server"]
    env:
      AWS_REGION: "us-east-1"
      CONNECT_INSTANCE_ID: "your-instance-id"
```

### Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "amazon-connect": {
      "command": "python",
      "args": ["-m", "amazon_connect_mcp.server"],
      "env": {
        "AWS_REGION": "us-east-1",
        "CONNECT_INSTANCE_ID": "your-instance-id"
      }
    }
  }
}
```

## Example: Place an Outbound Call

```python
# The AI agent simply calls:
connect_start_outbound_voice_contact(
    instance_id="12345678-abcd-...",
    destination_phone_number="+1-415-555-0100",
    contact_flow_id="flow-id-...",
    source_phone_number="+1-800-555-0123",
    attributes={
        "message": "Your appointment is tomorrow at 2 PM. Press 1 to confirm, 2 to reschedule."
    }
)
```

The contact flow reads `$.Attributes.message` and plays it via TTS.

## Deployment Options

### Default (TOLL_FREE, us-east-1)
```bash
./deploy.sh
```

### Custom
```bash
./deploy.sh --name my-contact-center --region us-west-2 --phone DID
```

### Destroy
```bash
./deploy.sh --destroy
```

## Cost (estimated, us-east-1)

| Component | Monthly |
|-----------|---------|
| Connect instance | Free |
| Phone number | ~$1-3 |
| Outbound calls | ~$0.018/min |
| Lambda | ~$0.20 (1M requests) |
| API Gateway | ~$3.50 (1M calls) |
| **Total (light)** | **~$5-10/mo** |

## File Structure

```
├── cloudformation/
│   └── infrastructure.yaml    # Single stack
├── src/
│   ├── amazon_connect_mcp/    # MCP server (48+ tools)
│   └── contact_flows/         # Contact flow tools
├── lambda/
│   └── connect_api_handler.py # Lambda bridge
├── tests/
│   └── test_outbound_harness.py
├── deploy.sh                  # One-liner deploy
├── README.md                  # This file
└── QUICKSTART.md              # Step-by-step guide
```

## License

MIT
