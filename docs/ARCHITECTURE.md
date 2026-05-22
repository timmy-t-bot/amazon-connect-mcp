# Amazon Connect MCP Server - Architecture Blueprint

**Version:** 1.0  
**Last Updated:** May 2026  
**Status:** Architectural Design Phase

---

## 1. Executive Summary

This document defines the architectural blueprint for the Amazon Connect MCP Server project. The server will enable AI agents (Hermes) to use Amazon Connect as an outbound communication platform with comprehensive infrastructure setup, contact flow management, and seamless integration capabilities.

### Key Differentiators

- **Infrastructure-First**: Unlike the community server (mundurragacl/amazon-connect-mcp) that focuses on operations, we prioritize "build-it-once" components
- **Complete API Coverage**: Direct MCP tools + Lambda/API Gateway bridge for missing APIs
- **Parameterized Contact Flows**: Dynamic outbound flow creation with customizable messages
- **Gap-Filling**: Addresses Phone Number claiming, Prompt management, and Instance lifecycle gaps

---

## 2. Research Findings

### 2.1 Community Server Analysis (mundurragacl/amazon-connect-mcp)

| Aspect | Details |
|--------|---------|
| **Repository** | https://github.com/mundurragacl/amazon-connect-mcp |
| **Stars** | 9 |
| **Tools** | 85+ tools across 9 categories |
| **Architecture** | Python + FastMCP + boto3 |
| **Focus** | Contact center operations, not infrastructure setup |

### 2.2 Existing Tool Categories (Community)

| Category | Tool Count | Direct APIs |
|----------|------------|-------------|
| **Core** | 9 | `connect` |
| **Contacts** | 8 | `connect` |
| **Config** | 17 | `connect` |
| **Analytics** | 5 | `connect` |
| **Profiles** | 9 | `customer-profiles` |
| **Campaigns** | 10 | `connect-campaigns` |
| **Cases** | 17 | `connectcases` |
| **AI** | 8 | `qconnect` |
| **Wizard/Templates** | 2 | N/A (Internal) |

### 2.3 Identified Gaps

#### **GAP 1: Phone Number Management**
- `search_available_phone_numbers` - NOT implemented
- `claim_phone_number` - NOT implemented
- `import_phone_number` - NOT implemented
- Community server only: `config_list_phone_numbers`, no claiming capability

#### **GAP 2: Prompt Management**
- `create_prompt` - NOT implemented
- `update_prompt` - NOT implemented
- `describe_prompt` - NOT implemented
- Community server: Prompts managed manually via console

#### **GAP 3: Instance Lifecycle**
- `create_instance` - NOT implemented
- `replicate_instance` - NOT implemented
- `delete_instance` - NOT implemented
- Community server: Assumes pre-existing instance

#### **GAP 4: Contact Flow Parameterization**
- Community: Creates flows but content is raw JSON
- Missing: Templated flows with variable substitution
- Missing: Parameterized outbound flows with custom messages

---

## 3. AWS Connect Service APIs

### 3.1 Service API Matrix

| Service | CLI Service | Priority | MCP Coverage | Lambda Bridge |
|---------|-------------|----------|--------------|---------------|
| **Amazon Connect** | `connect` | Critical | Direct | Limited (complex flows only) |
| **Connect Cases** | `connectcases` | High | Direct | No |
| **Customer Profiles** | `customer-profiles` | High | Direct | No |
| **Connect Campaigns v2** | `connectcampaignsv2` | High | Direct | No |
| **Amazon Q / QConnect** | `qconnect` | Medium | Direct | No |
| **Connect Contact Lens** | `connect-contact-lens` | Medium | Direct | No |
| **Connect WAF** | NA | Low | N/A | Terraform only |

### 3.2 Direct MCP Tools (No Bridge Needed)

The following Amazon Connect APIs have direct MCP tool coverage:

#### Core Contact Operations
- `connect:StartOutboundVoiceContact`
- `connect:StartChatContact`
- `connect:StartTaskContact`
- `connect:StopContact`
- `connect:TransferContact`
- `connect:UpdateContactAttributes`

#### Instance Management
- `connect:DescribeInstance`
- `connect:ListInstances`
- `connect:UpdateInstanceAttribute`

#### Contact Flows
- `connect:CreateContactFlow`
- `connect:UpdateContactFlowContent`
- `connect:DescribeContactFlow`
- `connect:ListContactFlows`

#### Queues
- `connect:CreateQueue`
- `connect:UpdateQueueStatus`
- `connect:DescribeQueue`
- `connect:ListQueues`

#### Users & Routing
- `connect:CreateUser`
- `connect:UpdateUserRoutingProfile`
- `connect:CreateRoutingProfile`
- `connect:AssociateQueueQuickConnects`

#### Hours of Operation
- `connect:CreateHoursOfOperation`
- `connect:UpdateHoursOfOperation`
- `connect:ListHoursOfOperations`

#### Campaigns
- `connect-campaigns:CreateCampaign`
- `connect-campaigns:StartCampaign`
- `connect-campaigns:PauseCampaign`
- `connect-campaigns:StopCampaign`

#### Cases
- `connectcases:CreateCase`
- `connectcases:GetCase`
- `connectcases:UpdateCase`
- `connectcases:ListDomains`
- `connectcases:CreateTemplate`

### 3.2 Lambda/API Gateway Bridge APIs

These APIs require the Lambda bridge due to complexity, statefulness, or missing AWS SDK support:

| API | Reason | Bridge Pattern |
|-----|--------|----------------|
| `connect:CreateInstance` | Multi-step, requires role/policy setup | Lambda workflow |
| `connect:ReplicateInstance` | Cross-region, long-running | Lambda + Step Functions |
| `connect:CreatePrompt` (SSML) | Audio synthesis, S3 dependencies | Lambda + S3 |
| `connect:UpdatePrompt` (SSML) | Audio file regeneration | Lambda + S3 |
| `connect:GetPromptFile` | S3 pre-signed URL retrieval | Lambda proxy |
| `connect:ListSecurityKeys` | Certificate management | Lambda wrapper |

### 3.3 Terraform/Gaps

These are NOT MCP tools but Infrastructure-as-Code:

- `aws_connect_instance` - Terraform only (IAM complexity)
- `aws_connect_phone_number` - Terraform/manual (regulatory restrictions)
- `aws_connect_quick_connect` - Terraform preferred
- `aws_connect_integration_association` - Terraform

---

## 4. Tool Taxonomy

### 4.1 Complete Tool Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMAZON CONNECT MCP SERVER                     │
│                    Target: 100+ Total Tools                      │
├─────────────────────────────────────────────────────────────────┤
│ TIER 1: Infrastructure & Setup (20 tools)                     │
│ ──────────────────────────────────────────────                  │
│ instance_*:                                                     │
│   - instance_list_instances (multi-region)                        │
│   - instance_describe_instance                                  │
│   - instance_create_instance [BRIDGE]                           │
│   - instance_replicate_instance [BRIDGE]                      │
│   - instance_update_instance_attribute                          │
│   - instance_delete_instance [BRIDGE]                         │
│                                                                 │
│ phone_numbers_*:                                                │
│   - phone_numbers_search_available                              │
│   - phone_numbers_claim_number [BRIDGE]                         │
│   - phone_numbers_list_numbers                                  │
│   - phone_numbers_associate_to_flow                             │
│   - phone_numbers_release_number                                │
│   - phone_numbers_import_number [BRIDGE]                        │
│                                                                 │
│ prompts_*:                                                      │
│   - prompts_list_prompts                                        │
│   - prompts_create_prompt [BRIDGE]                              │
│   - prompts_update_prompt [BRIDGE]                              │
│   - prompts_describe_prompt                                     │
│   - prompts_get_prompt_file [BRIDGE]                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: Configuration & Routing (25 tools)                        │
│ ───────────────────────────────────────────────────────────────   │
│ contact_flows_*:                                                 │
│   - contact_flows_list                                           │
│   - contact_flows_create                                         │
│   - contact_flows_create_outbound [TEMPLATED]                  │
│   - contact_flows_describe                                       │
│   - contact_flows_update_content                                 │
│   - contact_flows_delete                                         │
│   - contact_flows_create_version                                 │
│                                                                 │
│ queues_*:                                                       │
│   - queues_list_queues                                          │
│   - queues_create_queue                                           │
│   - queues_describe_queue                                         │
│   - queues_update_queue_status                                    │
│   - queues_update_queue_configs                                   │
│                                                                 │
│ hours_of_operation_*:                                           │
│   - hours_list_hours                                              │
│   - hours_create_hours                                            │
│   - hours_update_hours                                            │
│   - hours_create_override                                         │
│                                                                 │
│ routing_profiles_*:                                             │
│   - routing_list_profiles                                         │
│   - routing_create_profile                                        │
│   - routing_associate_queues                                      │
│                                                                 │
│ quick_connects_*:                                               │
│   - quick_connects_list                                           │
│   - quick_connects_create                                         │
│   - quick_connects_delete                                         │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3: Contacts & Operations (20 tools)                        │
│ ───────────────────────────────────────────────────────────────   │
│ contacts_*:                                                      │
│   - contacts_start_outbound_voice                               │
│   - contacts_start_outbound_chat                                │
│   - contacts_start_inbound_chat                                 │
│   - contacts_start_task                                           │
│   - contacts_stop_contact                                         │
│   - contacts_transfer                                             │
│   - contacts_update_attributes                                    │
│   - contacts_search_contacts                                      │
│   - contacts_describe_contact                                     │
│                                                                 │
│ recording_*:                                                    │
│   - recording_start_recording                                   │
│   - recording_stop_recording                                      │
│   - recording_suspend_recording                                   │
│   - recording_resume_recording                                    │
├─────────────────────────────────────────────────────────────────┤
│ TIER 4: Campaigns & Outbound (15 tools)                          │
│ ──────────────────────────────────────────────────────────────   │
│ campaigns_*:                                                     │
│   - campaigns_list_campaigns                                      │
│   - campaigns_create_campaign                                     │
│   - campaigns_describe_campaign                                   │
│   - campaigns_start_campaign                                      │
│   - campaigns_pause_campaign                                      │
│   - campaigns_resume_campaign                                     │
│   - campaigns_stop_campaign                                        │
│   - campaigns_delete_campaign                                      │
│   - campaigns_get_state                                            │
│   - campaigns_add_contacts                                         │
│   - campaigns_onboard_instance                                     │
│   - campaigns_check_onboarding_status                              │
├─────────────────────────────────────────────────────────────────┤
│ TIER 5: Cases & Agent Workspace (15 tools)                       │
│ ────────────────────────────────────────────────────────────   │
│ cases_*:                                                         │
│   - cases_list_domains                                           │
│   - cases_create_domain                                          │
│   - cases_list_templates                                          │
│   - cases_create_template                                         │
│   - cases_create_case                                             │
│   - cases_update_case                                             │
│   - cases_get_case                                                │
│   - cases_search_cases                                            │
│   - cases_create_field                                            │
│   - cases_list_fields                                             │
│                                                                 │
│ agent_status_*:                                                  │
│   - agent_status_list_statuses                                    │
│   - agent_status_create_status                                    │
│   - agent_status_put_user_status                                  │
│                                                                 │
│ users_*:                                                         │
│   - users_list_users                                               │
│   - users_create_user                                              │
│   - users_update_routing_profile                                   │
├─────────────────────────────────────────────────────────────────┤
│ TIER 6: Analytics & AI (8 tools)                                 │
│ ────────────────────────────────────────────────                 │
│ analytics_*:                                                     │
│   - analytics_get_current_metrics                                  │
│   - analytics_get_metric_data                                      │
│   - analytics_search_contacts                                      │
│                                                                 │
│ ai_qconnect_*:                                                   │
│   - ai_qconnect_list_knowledge_bases                             │
│   - ai_qconnect_query_assistant                                  │
│   - ai_qconnect_get_recommendations                                │
│   - ai_search_quick_responses                                      │
│                                                                 │
│ contact_lens_*:                                                  │
│   - contact_lens_list_realtime_segments                            │
├─────────────────────────────────────────────────────────────────┤
│ TIER 7: Lambda Bridge Operations (Internal)                      │
│ ─────────────────────────────────────────────────────────────     │
│ lambda_bridge_*:                                                  │
│   - lambda_create_instance_workflow                                │
│   - lambda_create_prompt_with_audio                              │
│   - lambda_replicate_instance_workflow                           │
│   - lambda_get_prompt_presigned_url                              │
│                                                                 │
│ TIER 8: Utility & Helper Tools (5 tools)                       │
│ ───────────────────────────────────────────────                 │
│ utils_*:                                                         │
│   - utils_validate_phone_number                                    │
│   - utils_format_contact_flow_json                               │
│   - utils_generate_ssml_prompt                                     │
│   - utils_get_instance_summary                                     │
│   - utils_check_prerequisites                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Tool Naming Convention

| Pattern | Example | Description |
|---------|---------|-------------|
| `{category}_{action}` | `contacts_start_outbound_voice` | Standard operation |
| `{category}_{resource}_{action}` | `queues_create_queue` | Resource-specific |
| `{service}_{category}_{action}` | `ai_qconnect_query_assistant` | AWS service prefix |
| `{resource}_{action}_{target}` | `phone_numbers_claim_number` | Target-specific action |
| `utils_{purpose}` | `utils_validate_phone_number` | Utility tools |

---

## 5. Lambda/API Gateway Bridge Architecture

### 5.1 Bridge Design Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP SERVER (Python)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Direct Tool │  │ Direct Tool │  │ Lambda Tool │             │
│  │ (boto3)     │  │ (boto3)     │  │ (HTTP Call) │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼───────────────────────┘
          │                │                │
          ▼                ▼                ▼
    ┌────────────┐   ┌────────────┐   ┌────────────┐
    │ AWS SDK    │   │ AWS SDK    │   │ API        │
    │ (boto3)    │   │ (boto3)    │   │ Gateway    │
    └────────────┘   └────────────┘   └──────┬─────┘
                                            │
                                   ┌────────▼────────┐
                                   │   Lambda        │
                                   │   Function      │
                                   │  ┌──────────┐  │
                                   │  │ Workflow │  │
                                   │  │ Handler  │  │
                                   │  └────┬─────┘  │
                                   └───────┼───────┘
                                           │
                             ┌─────────────┼─────────────┐
                             │             │             │
                             ▼             ▼             ▼
                       ┌──────────┐  ┌──────────┐  ┌──────────┐
                       │  Step    │  │   S3     │  │  AWS     │
                       │Functions │  │  Bucket  │  │ Connect  │
                       │(long-run)│  │(prompts) │  │   API    │
                       └──────────┘  └──────────┘  └──────────┘
```

### 5.2 Bridge Function Specifications

#### Function: `connect-instance-lifecycle`
- **Trigger**: API Gateway POST `/bridge/instance`
- **Purpose**: Create/Replicate/Delete Connect instances
- **Complexity**: Requires IAM role creation, S3 bucket setup, CloudWatch config
- **Input**: `action` (create/replicate/delete), `instance_alias`, `region`
- **Output**: Instance ARN, status, dashboard URL

#### Function: `connect-prompt-manager`
- **Trigger**: API Gateway POST `/bridge/prompt`
- **Purpose**: Create/update prompts with SSML support
- **Complexity**: Audio file generation, S3 upload, Connect API sync
- **Input**: `prompt_name`, `ssml_content` or `text`, `language`
- **Output**: Prompt ARN, S3 URL

#### Function: `connect-workflow-manager`
- **Trigger**: API Gateway POST `/bridge/workflow`
- **Purpose**: Multi-step operations (claim number + associate flow)
- **Complexity**: Transaction coordination across services
- **Input**: Workflow descriptor
- **Output**: Operation status, rollback capability

### 5.3 API Gateway Endpoints

| Endpoint | Method | Lambda | Purpose |
|----------|--------|--------|---------|
| `/bridge/instance` | POST | `instance-lifecycle` | Create/replicate/delete |
| `/bridge/prompt` | POST | `prompt-manager` | SSML prompt create/update |
| `/bridge/workflow` | POST | `workflow-manager` | Multi-step operations |
| `/bridge/status/{id}` | GET | `status-check` | Async operation status |
| `/bridge/rollback/{id}` | POST | `rollback-manager` | Undo failed operations |

---

## 6. Contact Flow Templates

### 6.1 Parameterized Outbound Flow Template

```json
{
  "Version": "2019-10-30",
  "StartAction": "PlayGreeting",
  "Actions": [
    {
      "Identifier": "PlayGreeting",
      "Type": "MessageParticipant",
      "Parameters": {
        "Text": "{{greeting_message}}",
        "SSML": "{{greeting_ssml}}"
      },
      "Transitions": {
        "NextAction": "WaitForResponse"
      }
    },
    {
      "Identifier": "WaitForResponse",
      "Type": "Wait",
      "Parameters": {
        "TimeoutSeconds": {{wait_timeout}}
      },
      "Transitions": {
        "TimeoutAction": "Disconnect",
        "NextAction": "CheckIntent"
      }
    },
    {
      "Identifier": "CheckIntent",
      "Type": "GetUserInput",
      "Parameters": {
        "Text": "{{confirmation_question}}",
        "LexV2Bot": {
          "AliasArn": "{{lex_bot_arn}}"
        }
      },
      "Transitions": {
        "NextAction": "ProcessIntent"
      }
    },
    {
      "Identifier": "ProcessIntent",
      "Type": "InvokeLambdaFunction",
      "Parameters": {
        "LambdaFunctionARN": "{{lambda_arn}}",
        "InvocationTimeLimitSeconds": 8
      },
      "Transitions": {
        "NextAction": "PlayConfirmation"
      }
    },
    {
      "Identifier": "PlayConfirmation",
      "Type": "MessageParticipant",
      "Parameters": {
        "Text": "{{confirmation_reply}}"
      },
      "Transitions": {
        "NextAction": "SetAttributes"
      }
    },
    {
      "Identifier": "SetAttributes",
      "Type": "UpdateContactAttributes",
      "Parameters": {
        "Attributes": {
          "call_result": "{{call_result}}",
          "callback_requested": "{{callback_needed}}"
        }
      },
      "Transitions": {
        "NextAction": "Disconnect"
      }
    },
    {
      "Identifier": "Disconnect",
      "Type": "DisconnectParticipant",
      "Parameters": {}
    }
  ],
  "Variables": {
    "greeting_message": {
      "type": "string",
      "required": true,
      "description": "Message to play when call connects",
      "ssml_enabled": true
    },
    "greeting_ssml": {
      "type": "string",
      "required": false,
      "description": "SSML version of greeting for better TTS"
    },
    "wait_timeout": {
      "type": "integer",
      "default": 5,
      "min": 1,
      "max": 30,
      "description": "Seconds to wait for user response"
    },
    "confirmation_question": {
      "type": "string",
      "required": true,
      "description": "Question to ask user for confirmation"
    },
    "confirmation_reply": {
      "type": "string",
      "required": true,
      "description": "Response to user confirmation"
    },
    "lex_bot_arn": {
      "type": "arn",
      "required": false,
      "description": "Lex bot for intent recognition"
    },
    "lambda_arn": {
      "type": "arn",
      "required": true,
      "description": "Lambda for custom business logic"
    },
    "call_result": {
      "type": "enum",
      "values": ["SUCCESS", "NO_ANSWER", "BUSY", "FAILED"],
      "default": "SUCCESS"
    },
    "callback_needed": {
      "type": "boolean",
      "default": false
    }
  }
}
```

### 6.2 Template Engine

The MCP server will implement a template engine at `src/amazon_connect_mcp/templates/`:

```python
# Template engine pseudocode

templates/
├── __init__.py
├── engine.py           # Template rendering engine
├── registry.py         # Template registration
├── outbound/
│   ├── basic_notification.json
│   ├── appointment_reminder.json
│   ├── survey_invitation.json
│   └── payment_reminder.json
├── inbound/
│   ├── basic_ivr.json
│   └── callback_request.json
└── shared/
    ├── modules/
    │   ├── validate_input.json
    │   └── log_to_s3.json
    └── snippets/
        ├── greeting.json
        └── farewell.json
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Project structure setup
- [ ] Core MCP server with FastMCP
- [ ] AWS SDK client abstractions
- [ ] Direct tool categories: contacts, analytics
- [ ] Basic connection tests

### Phase 2: Infrastructure (Weeks 3-4)
- [ ] Instance management tools
- [ ] Lambda bridge setup (API Gateway + Lambda)
- [ ] Phone numbers bridge APIs
- [ ] Prompt management bridge
- [ ] Infrastructure validation tests

### Phase 3: Configuration (Weeks 5-6)
- [ ] Contact flow CRUD tools
- [ ] Queue and routing configuration
- [ ] Hours of operation management
- [ ] Template engine implementation
- [ ] Parameterized flow creation

### Phase 4: Operations (Weeks 7-8)
- [ ] Campaigns integration
- [ ] Cases integration
- [ ] Agent status tracking
- [ ] Recording management
- [ ] Real-time metrics

### Phase 5: AI & Polish (Weeks 9-10)
- [ ] QConnect integration
- [ ] Contact Lens analytics
- [ ] Documentation and guides
- [ ] Integration tests
- [ ] Performance optimization

---

## 8. Security Considerations

### 8.1 IAM Permissions Model

#### MCP Server Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ConnectCoreAccess",
      "Effect": "Allow",
      "Action": [
        "connect:*",
        "connectcases:*",
        "connect-campaigns:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LambdaBridgeInvoke",
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction",
        "apigateway:GET"
      ],
      "Resource": "arn:aws:lambda:*:*:function:connect-bridge-*"
    }
  ]
}
```

#### Lambda Bridge Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ConnectInstanceManagement",
      "Effect": "Allow",
      "Action": [
        "connect:CreateInstance",
        "connect:DeleteInstance",
        "connect:ReplicateInstance"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMForInstance",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:AttachRolePolicy"
      ],
      "Resource": "arn:aws:iam::*:role/connect-*",
      "Condition": {
        "StringLikeIfExists": {
          "iam:PolicyName": ["Connect*"]
        }
      }
    }
  ]
}
```

### 8.2 Data Protection

- **Phone Numbers**: Masked in logs (E.164 format shown only on success)
- **Audio Files**: Encrypted at rest in S3 (SSE-KMS)
- **SSML Content**: Not logged in plain text (hash only)
- **Tokens**: Rotated every 24 hours

---

## 9. Testing Strategy

### 9.1 Unit Tests
- Mock all AWS SDK calls
- Test template rendering
- Validate parameter substitution

### 9.2 Integration Tests
```python
# Example integration test
async def test_outbound_flow_creation():
    # Create test flow
    flow = await config_create_contact_flow(
        name="test_outbound_{{timestamp}}",
        template="outbound_appointment",
        params={"greeting": "Hello from test"}
    )
    
    # Verify flow content
    assert flow.status == "ACTIVE"
    
    # Cleanup
    await config_delete_contact_flow(flow.id)
```

### 9.3 End-to-End Tests
- Full call flow: Claim number → Create flow → Make call → Verify
- Campaign flow: Onboard → Create → Add contacts → Start → Verify
- Error scenarios: Wrong region, invalid permissions, rate limiting

---

## 10. References

### AWS Documentation
- [Amazon Connect API](https://docs.aws.amazon.com/connect/latest/APIReference/Welcome.html)
- [ConnectCases API](https://docs.aws.amazon.com/connect/latest/case-api/Welcome.html)
- [ConnectCampaigns v2](https://docs.aws.amazon.com/connect-campaigns/latest/APIReference/Welcome.html)
- [QConnect API](https://docs.aws.amazon.com/amazonq/latest/connect-api/Welcome.html)

### Community Resources
- [mundurragacl/amazon-connect-mcp](https://github.com/mundurragacl/amazon-connect-mcp) - Reference implementation
- [awslabs/mcp](https://github.com/awslabs/mcp) - AWS MCP servers (no Connect)
- [MCP Specification](https://modelcontextprotocol.io/specification/)

### Related Skills
- `/home/mike/.hermes/skills/mcp/native-mcp/references/amazon-connect-mcp.md` - Prior research

---

## 11. Appendix

### A. Resource ARN Formats

| Resource | ARN Format |
|----------|-----------|
| Instance | `arn:aws:connect:{region}:{account-id}:instance/{instance-id}` |
| Contact Flow | `arn:aws:connect:{region}:{account-id}:instance/{instance-id}/contact-flow/{flow-id}` |
| Queue | `arn:aws:connect:{region}:{account-id}:instance/{instance-id}/queue/{queue-id}` |
| Phone Number | `arn:aws:connect:{region}:{account-id}:phone-number/{phone-number-id}` |
| Prompt | `arn:aws:connect:{region}:{account-id}:instance/{instance-id}/prompt/{prompt-id}` |

### B. Service Quotas (Reference)

| Resource | Default Limit |
|----------|--------------|
| Contacts per second | 100 |
| Queues per instance | 50 |
| Contact flows per instance | 200 |
| Phone numbers per instance | 100 |
| Prompts per instance | 250 |
| Concurrent calls | Varies by instance |