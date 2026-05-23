# Amazon Connect MCP Server — Architecture

## Overview

A Model Context Protocol (MCP) server that lets AI agents manage Amazon Connect and place outbound voice calls with dynamic messages — deployed in one command.

---

## Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         AI AGENT OR CLIENT                                │
│  (Hermes, Claude, Cursor, Amazon Q, any MCP client)                     │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ STDIO or SSE (MCP Protocol)
┌──────────────────────────────▼───────────────────────────────────────────┐
│                    AMAZON CONNECT MCP SERVER                              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  FastMCP Python Server                                               │ │
│  │  • 48+ MCP tools registered                                        │ │
│  │  • Direct boto3 calls to AWS APIs                                   │ │
│  │  • Contact flow templates (JSON with {{variable}} substitution)     │ │
│  │  • Lambda API bridge for extended operations (phone claiming, etc.)   │ │
│  └──────────────────────────────┬───────────────────────────────────────┘ │
└───────────────────────────────┼───────────────────────────────────────────┘
                                │ boto3
┌───────────────────────────────▼───────────────────────────────────────────┐
│                  AWS CLOUDFORMATION SINGLE STACK                           │
│  ┌──────────────────────────┐  ┌──────────────────────────┐               │
│  │  Amazon Connect Instance │  │  Lambda + API Gateway    │               │
│  │  • Instance + Alias      │  │  • Python 3.12 handler   │               │
│  │  • Phone Number          │  │  • REST API endpoints     │               │
│  │  • Default Queue         │  │  • CORS enabled           │               │
│  │  • Hours of Operation    │  │  • CloudWatch logs        │               │
│  │  • Outbound Contact Flow │  │                           │               │
│  └────────────────────┬─────┘  └────────────────────┬────┘               │
│                       │                              │                    │
│  ┌────────────────────▼──────┐  ┌───────────────────▼────┐              │
│  │  IAM Role (Least Privilege)│  │  CloudWatch Logs       │              │
│  │  • connect:*               │  │  • 14-day retention    │              │
│  │  • lambda:Invoke           │  │  • Auto-cleanup        │              │
│  │  • apigateway:Invoke       │  │                        │              │
│  └────────────────────────────┘  └────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────────┐
│                         CUSTOMER PHONE                                    │
│  • Receives TTS message from contact flow                                  │
│  • Can press DTMF (1=confirm, 2=decline) if interactive mode            │
│  • Attributes (message, etc.) passed via $.Attributes.<key>                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## How Data Flows

### 1. Deploy (One Command)

```
User runs: ./deploy.sh 
    → Checks AWS credentials
    → Creates CloudFormation stack (5 min)
    → Auto-claims phone number
    → Tests /health endpoint
    → Outputs MCP config JSON (copy-paste ready)
```

### 2. Place Outbound Call (AI Agent)

```
AI Agent calls MCP tool:
    connect_start_outbound_voice_contact(
        instance_id="1234...",
        destination_phone_number="+14155550100",
        contact_flow_id="abcdef...",
        source_phone_number="+18005550100",
        attributes={
            "message": "Hi John, your appointment tomorrow at 2PM. Press 1 to confirm."
        }
    )

    → boto3 → connect:StartOutboundVoiceContact
    → AWS dials customer
    → Contact flow executes
    → PlayPrompt reads $.Attributes.message
    → GetParticipantInput listens for 1 or 2
    → Stores disposition in contact attributes
```

### 3. Manage Infrastructure (AI Agent)

```
AI Agent queries:
    connect_list_instances()          → All Connect instances
    connect_list_queues(instance_id)    → All queues
    connect_list_phone_numbers(...)    → Claimed numbers
    connect_search_available_numbers(...) → Find new toll-free/DID numbers
    connect_claim_phone_number(...)   → Claim a number
    contact_flows_create_outbound(...) → Create new outbound flow from template
```

---

## File Layout

```
amazon-connect-mcp/
│
│── deploy.sh                          ← Main entry point (1-liner)
│── cloudformation/
│   └── infrastructure.yaml              ← Single stack: everything
│
│── src/
│   ├── amazon_connect_mcp/
│   │   ├── server.py                    ← FastMCP registration (48 tools)
│   │   ├── config.py                    ← Env/config loader
│   │   ├── connect_api_bridge.py        ← Lambda-backed extended APIs
│   │   │
│   │   ├── components/                    ← Direct boto3 tools
│   │   │   ├── instance_manager.py      ← create, describe, list, delete instance
│   │   │   ├── queues.py                ← queue CRUD
│   │   │   ├── phone_numbers.py         ← search, claim, release, list
│   │   │   ├── hours_of_operation.py    ← hours CRUD
│   │   │   ├── prompts.py               ← prompt CRUD
│   │   │   ├── outbound.py              ← ⭐ StartOutboundVoiceContact + Attributes
│   │   │   ├── routing_profiles.py      ← list, describe
│   │   │   ├── users.py                 ← list, describe
│   │   │   └── integration.py           ← component catalog
│   │   │
│   │   └── templates/                   ← Contact flow JSON templates
│   │       ├── engine.py                ← Load, render, validate templates
│   │       ├── registry.py              ← Template catalog
│   │       └── outbound/
│   │           ├── universal_outbound.json      ← ⭐ Master outbound flow
│   │           ├── ai_agent_outbound.json       ← Bedrock/Lex interactive
│   │           ├── play_prompt_outbound.json      ← Simple play + hangup
│   │           ├── appointment_reminder.json      ← Appointment-specific
│   │           └── payment_reminder.json        ← Payment-specific
│   │
│   └── contact_flows/
│       ├── contact_flow_tools.py        ← create, update, delete flows
│       └── __init__.py
│
│── lambda/
│   ├── connect_api_handler.py           ← Lambda entry (bridge)
│   ├── openapi.yaml                     ← REST API spec
│   └── requirements.txt                 ← boto3, fastmcp deps
│
│── tests/
│   ├── test_server.py                   ← MCP tool registration tests
│   ├── test_contact_flows.py            ← Flow CRUD tests
│   ├── test_outbound_harness.py         ← ⭐ Outbound call + attribute tests
│   └── test_components.py               ← Component tool tests
│
│── docs/
│   ├── ARCHITECTURE.md                  ← This doc
│   ├── API_REFERENCE.md                 ← All tool descriptions
│   ├── HERMES_SETUP.md                ← Hermes agent config
│   └── LAMBDA_BRIDGE_SPEC.md            ← REST API docs
│
│── README.md                            ← 1-liner deploy + quick start
│── QUICKSTART.md                        ← Copy-paste config snippets
│── pyproject.toml                       ← Python packaging
│── requirements.txt                     ← Dependencies
│── LICENSE                              ← MIT
│── .gitignore
│
└── scripts/
    ├── validate.py                      ← Pre-flight checks (AWS, Python, deps)
    └── setup.sh                         ← First-time developer env setup
```

---

## CloudFormation Stack Detail

### Resources Created

| # | Resource | Type | Notes |
|---|----------|------|-------|
| 1 | Connect Instance | `AWS::Connect::Instance` | Alias + Identity management type |
| 2 | Default Queue | `AWS::Connect::Queue` | Named "MCP Default Queue" |
| 3 | Hours of Operation | `AWS::Connect::HoursOfOperation` | Mon-Fri 9AM-5PM ET |
| 4 | Outbound Contact Flow | `AWS::Connect::ContactFlow` | Uses universal template JSON |
| 5 | Lambda Function | `AWS::Lambda::Function` | Python 3.12, inline code |
| 6 | IAM Role | `AWS::IAM::Role` | Least-privilege, Connect + Lambda + CloudWatch |
| 7 | API Gateway | `AWS::ApiGateway::RestApi` | `{proxy+}` route + OPTIONS |
| 8 | Lambda Permission | `AWS::Lambda::Permission` | API Gateway → Lambda invoke |
| 9 | CloudWatch Log Group | `AWS::Logs::LogGroup` | 14-day retention |
| 10 | Phone Number | Lambda-custom | Auto-claimed during deploy |

### Stack Outputs

| Output | Value |
|--------|-------|
| `ConnectInstanceId` | Instance UUID |
| `ConnectInstanceArn` | Instance ARN |
| `ApiGatewayUrl` | `https://xxx.execute-api.region.amazonaws.com/prod` |
| `LambdaFunctionArn` | Lambda ARN |
| `McpServerConfig` | Ready-to-paste JSON for MCP clients |
| `PhoneNumberClaimed` | The claimed number |
| `ContactFlowId` | Outbound flow ID |

---

## Tool Inventory

### Outbound Communication (4 tools)
| Tool | API | Key Feature |
|------|-----|-------------|
| `connect_start_outbound_voice_contact` | `connect:StartOutboundVoiceContact` | ⭐ Supports `Attributes={}` dict for dynamic messages |
| `connect_stop_contact` | `connect:StopContact` | End active call |
| `connect_describe_contact` | `connect:DescribeContact` | Get call details |
| `connect_update_contact_attributes` | `connect:UpdateContactAttributes` | Change attrs mid-call |

### Instance Management (5 tools)
| Tool | API | Key Feature |
|------|-----|-------------|
| `connect_instances_list` | `connect:ListInstances` | All regions |
| `connect_instances_describe` | `connect:DescribeInstance` | Detail view |
| `connect_instances_create` | `connect:CreateInstance` | One-time setup |
| `connect_instances_update` | `connect:UpdateInstanceAttribute` | Modify settings |
| `connect_instances_delete` | `connect:DeleteInstance` | ⚠️ Teardown |

### Phone Numbers (6 tools)
| Tool | API | Key Feature |
|------|-----|-------------|
| `connect_phone_numbers_search` | `connect:SearchAvailablePhoneNumbers` | Find toll-free / DID |
| `connect_phone_numbers_claim` | `connect:ClaimPhoneNumber` | Assign number |
| `connect_phone_numbers_release` | `connect:ReleasePhoneNumber` | ⚠️ Remove number |
| `connect_phone_numbers_list` | `connect:ListPhoneNumbers` | Show claimed |
| `connect_phone_numbers_describe` | `connect:DescribePhoneNumber` | Details |
| `connect_phone_numbers_update` | `connect:UpdatePhoneNumber` | Modify |

### Queues (6 tools)
| Tool | API |
|------|-----|
| `connect_queues_list` | `connect:ListQueues` |
| `connect_queues_describe` | `connect:DescribeQueue` |
| `connect_queues_create` | `connect:CreateQueue` |
| `connect_queues_update` | `connect:UpdateQueue` |
| `connect_queues_delete` | `connect:DeleteQueue` |
| `connect_queues_update_name` | `connect:UpdateQueueName` |

### Hours of Operation (8 tools)
| Tool | API |
|------|-----|
| `connect_hours_of_operations_list` | `connect:ListHoursOfOperations` |
| `connect_hours_of_operations_describe` | `connect:DescribeHoursOfOperation` |
| `connect_hours_of_operations_create` | `connect:CreateHoursOfOperation` |
| `connect_hours_of_operations_update` | `connect:UpdateHoursOfOperation` |
| `connect_hours_of_operations_delete` | `connect:DeleteHoursOfOperation` |
| `connect_hours_of_operations_create_override` | `connect:CreateHoursOfOperationOverride` |
| `connect_hours_of_operations_delete_override` | `connect:DeleteHoursOfOperationOverride` |
| `connect_hours_of_operations_describe_override` | `connect:DescribeHoursOfOperationOverride` |

### Prompts (4 tools)
| Tool | API |
|------|-----|
| `connect_prompts_list` | `connect:ListPrompts` |
| `connect_prompts_describe` | `connect:DescribePrompt` |
| `connect_prompts_create` | `connect:CreatePrompt` |
| `connect_prompts_delete` | `connect:DeletePrompt` |

### Contact Flows (12 tools via `contact_flow_tools.py`)
| Tool | Key Feature |
|------|-------------|
| `contact_flows_create_outbound` | ⭐ Template-driven with parameters |
| `contact_flows_create` | Raw JSON |
| `contact_flows_update_from_template` | Re-render template |
| `contact_flows_list` | List all |
| `contact_flows_describe` | Detail view |
| `contact_flows_delete` | Remove |
| `contact_flows_update_content` | Patch JSON |
| `contact_flows_search` | Filter/search |
| `contact_flows_list_templates` | Available templates |
| `contact_flows_get_template_schema` | Parameter schema |
| `contact_flows_validate_parameters` | Pre-check |
| `contact_flows_create_version` | Versioning |

### Routing Profiles (2 tools)
| Tool | API |
|------|-----|
| `connect_routing_profiles_list` | `connect:ListRoutingProfiles` |
| `connect_routing_profiles_describe` | `connect:DescribeRoutingProfile` |

### Users (2 tools)
| Tool | API |
|------|-----|
| `connect_users_list` | `connect:ListUsers` |
| `connect_users_describe` | `connect:DescribeUser` |

**Total: 48+ tools**

---

## Cost Breakdown

| Component | AWS Pricing | Est. Monthly (light usage) |
|-----------|------------|---------------------------|
| Connect Instance | Free | $0 |
| Phone Number (Toll-Free US) | $0.10-$1.25 | ~$1 |
| Phone Number (DID US) | $1.00-$3.00 | ~$2 |
| Outbound Minutes | ~$0.018/min | $18 (1,000 min) |
| Lambda Requests | $0.20/million | ~$0.20 |
| API Gateway | $3.50/million | ~$3.50 |
| CloudWatch Logs | $0.50/GB ingested | ~$0.50 |
| CloudFormation | Free | $0 |
| **Total** | | **~$25-30/mo** |

---

## Security Model

### Identity
- No long-term credentials stored in code
- Uses standard AWS credential chain:
  1. `~/.aws/credentials` profile
  2. Environment variables (AWS_ACCESS_KEY_ID, etc.)
  3. IAM role (if running on EC2/ECS/Lambda)

### IAM Permissions (Least Privilege)
- `connect:*` scoped to instance where possible
- `lambda:InvokeFunction` only on own function
- CloudWatch write only to own log group
- No `iam:*`, `s3:*`, or cross-account access

### Data Handling
- No PII stored in MCP server
- All API calls are real-time to AWS
- Connect encrypts call recordings at rest (KMS)
- Contact attributes only persist during call (or sent to Kinesis if configured)

---

## Extensibility

### Add a New Contact Flow Template

```bash
# 1. Create JSON in templates/outbound/my_flow.json
# 2. Use {{variable_name}} placeholders  
# 3. Register in templates/registry.py
# 4. Call via MCP:
contact_flows_create_outbound(
    instance_id="...",
    name="My Flow",
    mode="PLAY_PROMPT",
    parameters={"variable_name": "Hello!"}
)
```

### Add a New Lambda Bridge API

Add to `lambda/connect_api_handler.py`:
```python
elif action == 'my_new_action':
    result = connect.my_new_api(**params)
    return response(200, result)
```
Then register as MCP tool in `src/amazon_connect_mcp/connect_api_bridge.py`.

### Add a New Direct boto3 Tool

Add to existing component or create `components/new_service.py`, then register in `server.py`:
```python
from .components.new_service import connect_new_tool
mcp.tool()(connect_new_tool)
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| **CloudFormation over Terraform** | Native AWS, no extra dependencies, one AWS CLI command |
| **Lambda inline code** | No S3 bucket needed for deployment |
| **Single `{proxy+}` API Gateway route** | Simpler than 15+ individual methods, zero ordering issues |
| **Template engine with `{{variable}}` substitution** | Human-readable, no Jinja2 dependency, works with raw JSON |
| **boto3 direct instead of all via Lambda** | Faster, fewer Lambda cold starts, simpler debugging |
| **Contact flow JSON stored as files** | Version controlled, diffable, reviewable |
| **FastMCP stdio default** | Works with Claude, Cursor, Hermes, VS Code — no network config |
| **No stored credentials** | AWS credential chain handles rotation, profiles, SSO |
| **MIT license** | Matches community upstream (`mundurragacl/amazon-connect-mcp`) |

---

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Core infrastructure + one-liner deploy | ✅ Done |
| 2 | Outbound voice with attributes | ✅ Done |
| 3 | Template engine + universal flows | ✅ Done |
| 4 | Bedrock Agent / Lex integration | ✅ Done |
| 5 | EventBridge webhooks (real-time call events) | 📋 Planned |
| 6 | Amazon Q Connect integration (AI agent) | 📋 Planned |
| 7 | Contact Lens analytics + transcripts | 📋 Planned |
| 8 | Multi-region Connect instance replication | 📋 Future |

---

## Reference

- **GitHub**: https://github.com/timmy-t-bot/amazon-connect-mcp
- **MCP Spec**: https://modelcontextprotocol.io
- **Amazon Connect API**: https://docs.aws.amazon.com/connect/latest/APIReference/
- **Inspiration**: https://github.com/mundurragacl/amazon-connect-mcp (operations-focused)
- **Deploy**: `./deploy.sh --help`
