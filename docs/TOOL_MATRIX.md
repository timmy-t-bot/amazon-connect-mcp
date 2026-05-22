# Amazon Connect MCP Server - Gap Analysis & Tool Matrix

## Research Summary

| Source | Tools | Primary Focus | Infrastructure | Operations |
|--------|-------|---------------|----------------|------------|
| **mundurragacl/amazon-connect-mcp** | 85+ | Contact center operations | Minimal | Yes (Full) |
| **AWS Labs MCP** | 58 services | Service-specific | Varies | Varies |
| **Our Target** | 100+ | Infrastructure + Operations | Full | Yes (Full) |

---

## Complete Tool Mapping

### Legend
- ✅ Direct MCP Tool (boto3)
- 🔶 Lambda Bridge Required
- 🏗️ Terraform/IaC (Not MCP)
- ❌ Not Implemented (Gap)

### 1. Instance Management

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_instances` | ✅ | ✅ | Direct | Multi-region, paginated |
| `describe_instance` | ✅ | ✅ | Direct | Status, ARN, config |
| `create_instance` | ❌ | 🔶 | Bridge | IAM, S3, CloudWatch setup |
| `replicate_instance` | ❌ | 🔶 | Bridge | Cross-region DR |
| `delete_instance` | ❌ | 🔶 | Bridge | Cleanup coordination |
| `update_instance_attribute` | Partial | ✅ | Direct | Feature flags |
| `get_instance_summary` | ❌ | ✅ | Direct | Aggregated status |

### 2. Phone Numbers

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `search_available_phone_numbers` | ❌ | 🔶 | Bridge | DIDs/Toll-free search |
| `claim_phone_number` | ❌ | 🔶 | Bridge | Requires IAM + approval |
| `import_phone_number` | ❌ | 🔶 | Bridge | From other account |
| `release_phone_number` | ❌ | ✅ | Direct | Unclaim number |
| `list_phone_numbers` | ✅ | ✅ | Direct | Paginated list |
| `associate_phone_number_to_flow` | ❌ | ✅ | Direct | Link to contact flow |
| `update_phone_number` | ❌ | ✅ | Direct | Metadata updates |
| `describe_phone_number` | ❌ | ✅ | Direct | Details + status |

### 3. Prompts & Audio

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_prompts` | ❌ | ✅ | Direct | Text + audio prompts |
| `create_prompt` (Text) | ❌ | ✅ | Direct | Simple text prompts |
| `create_prompt` (SSML) | ❌ | 🔶 | Bridge | Audio synthesis |
| `update_prompt` | ❌ | 🔶 | Bridge | Re-synthesize |
| `describe_prompt` | ❌ | ✅ | Direct | Metadata + content |
| `delete_prompt` | ❌ | ✅ | Direct | Remove prompt |
| `get_prompt_file` | ❌ | 🔶 | Bridge | S3 pre-signed |

### 4. Contact Flows

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_contact_flows` | ✅ | ✅ | Direct | All flow types |
| `create_contact_flow` (Raw) | ✅ | ✅ | Direct | JSON flow definition |
| `create_contact_flow` (Template) | ❌ | 🔶 | Bridge | Parameterized templates |
| `create_outbound_flow` | ❌ | 🔶 | Bridge | Message + logic |
| `describe_contact_flow` | ✅ | ✅ | Direct | Flow content |
| `update_contact_flow_content` | ✅ | ✅ | Direct | Modify logic |
| `create_flow_version` | ❌ | ✅ | Direct | Versioning |
| `delete_contact_flow` | ❌ | ✅ | Direct | Remove flow |
| `search_contact_flows` | ❌ | ✅ | Direct | Filter flows |

### 5. Queues

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_queues` | ✅ | ✅ | Direct | All queues |
| `create_queue` | ✅ | ✅ | Direct | Requires hours ID |
| `describe_queue` | ✅ | ✅ | Direct | Metrics + config |
| `update_queue_status` | ✅ | ✅ | Direct | Enable/disable |
| `update_queue_config` | ❌ | ✅ | Direct | Routing, callbacks |
| `delete_queue` | ❌ | ✅ | Direct | Remove queue |
| `search_queues` | ❌ | ✅ | Direct | Filter queues |

### 6. Hours of Operation

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_hours_of_operations` | ✅ | ✅ | Direct | All schedules |
| `create_hours_of_operation` | ✅ | ✅ | Direct | Weekly schedule |
| `describe_hours_of_operation` | ❌ | ✅ | Direct | Config details |
| `update_hours_of_operation` | ❌ | ✅ | Direct | Modify schedule |
| `create_hours_override` | ❌ | ✅ | Direct | Holiday/exception |
| `delete_hours_of_operation` | ❌ | ✅ | Direct | Remove schedule |

### 7. Routing Profiles

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_routing_profiles` | ✅ | ✅ | Direct | All profiles |
| `create_routing_profile` | ✅ | ✅ | Direct | Channel concurrency |
| `describe_routing_profile` | ❌ | ✅ | Direct | Config details |
| `update_routing_profile` | ❌ | ✅ | Direct | Modify queues |
| `associate_queues` | ❌ | ✅ | Direct | Link to queues |
| `delete_routing_profile` | ❌ | ✅ | Direct | Remove profile |

### 8. Users & Agents

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_users` | ✅ | ✅ | Direct | Paginated |
| `create_user` | ✅ | ✅ | Direct | Agent account |
| `describe_user` | ✅ | ✅ | Direct | Config + status |
| `update_user_routing_profile` | ✅ | ✅ | Direct | Change routing |
| `update_user_security_profiles` | ❌ | ✅ | Direct | Permissions |
| `update_user_hierarchy` | ❌ | ✅ | Direct | Org placement |
| `delete_user` | ❌ | ✅ | Direct | Remove account |
| `search_users` | ❌ | ✅ | Direct | Filter agents |

### 9. Agent Status

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_agent_statuses` | ✅ | ✅ | Direct | Custom statuses |
| `create_agent_status` | ❌ | ✅ | Direct | Break, Lunch, etc |
| `describe_agent_status` | ❌ | ✅ | Direct | Config |
| `put_user_status` | ✅ | ✅ | Direct | Set current status |

### 10. Contacts & Calls

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `start_outbound_voice_contact` | ✅ | ✅ | Direct | Place call |
| `start_outbound_chat_contact` | ❌ | ✅ | Direct | Outbound chat |
| `start_chat_contact` | ✅ | ✅ | Direct | Inbound chat |
| `start_task_contact` | ✅ | ✅ | Direct | Create task |
| `describe_contact` | ❌ | ✅ | Direct | Call details |
| `search_contacts` | ❌ | ✅ | Direct | Filter history |
| `stop_contact` | ✅ | ✅ | Direct | End call |
| `transfer_contact` | ✅ | ✅ | Direct | Queue/agent |
| `update_contact_attributes` | ✅ | ✅ | Direct | Custom data |
| `suspend_contact` | ❌ | ✅ | Direct | Hold processing |
| `resume_contact` | ❌ | ✅ | Direct | Resume processing |

### 11. Recording

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `start_contact_recording` | ✅ | ✅ | Direct | Begin recording |
| `stop_contact_recording` | ✅ | ✅ | Direct | End recording |
| `suspend_contact_recording` | ❌ | ✅ | Direct | Pause recording |
| `resume_contact_recording` | ❌ | ✅ | Direct | Resume recording |

### 12. Campaigns (Outbound)

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_campaigns` | ✅ | ✅ | Direct | All campaigns |
| `create_campaign` | ✅ | ✅ | Direct | Config + schedule |
| `describe_campaign` | ✅ | ✅ | Direct | Details |
| `start_campaign` | ✅ | ✅ | Direct | Begin dialing |
| `pause_campaign` | ✅ | ✅ | Direct | Pause dialing |
| `resume_campaign` | ✅ | ✅ | Direct | Resume dialing |
| `stop_campaign` | ✅ | ✅ | Direct | End campaign |
| `get_campaign_state` | ✅ | ✅ | Direct | Current state |
| `add_contacts_to_campaign` | ✅ | ✅ | Direct | Dial list mgmt |
| `onboard_campaigns` | ❌ | 🔶 | Bridge | Instance enablement |
| `check_onboarding_status` | ❌ | 🔶 | Bridge | KMS + S3 setup |

### 13. Cases

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_cases_domains` | ✅ | ✅ | Direct | Case domains |
| `create_cases_domain` | ✅ | ✅ | Direct | Enable cases |
| `list_case_templates` | ✅ | ✅ | Direct | All templates |
| `create_case_template` | ✅ | ✅ | Direct | Field definitions |
| `create_case` | ✅ | ✅ | Direct | New case |
| `get_case` | ✅ | ✅ | Direct | Case details |
| `update_case` | ✅ | ✅ | Direct | Modify case |
| `search_cases` | ✅ | ✅ | Direct | Filter cases |
| `list_case_fields` | ❌ | ✅ | Direct | Custom fields |
| `create_case_field` | ❌ | ✅ | Direct | Add fields |
| `create_related_item` | ❌ | ✅ | Direct | Link contact |

### 14. QConnect (AI)

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `list_knowledge_bases` | ✅ | ✅ | Direct | Knowledge stores |
| `query_assistant` | ✅ | ✅ | Direct | Get AI answers |
| `get_recommendations` | ❌ | ✅ | Direct | Real-time suggestions |
| `list_quick_responses` | ❌ | ✅ | Direct | Canned responses |
| `create_quick_response` | ❌ | ✅ | Direct | Add response |
| `search_content` | ❌ | ✅ | Direct | KB search |
| `create_session` | ❌ | ✅ | Direct | AI session |

### 15. Analytics & Metrics

| Tool | Community | Ours | Method | Notes |
|------|-----------|------|--------|-------|
| `get_current_metrics` | ✅ | ✅ | Direct | Real-time data |
| `get_metric_data` | ❌ | ✅ | Direct | Historical data |
| `get_current_user_data` | ❌ | ✅ | Direct | Agent status |
| `search_contacts` | ❌ | ✅ | Direct | History search |
| `list_realtime_contact_analysis` | ❌ | ✅ | Direct | Contact Lens |

---

## Gap Summary by Category

### Critical Gaps Filled (Lambda Bridge)

| # | Feature | User Impact | Priority |
|---|---------|-------------|----------|
| 1 | **Phone Number Claiming** | Users can't claim numbers via MCP | P0 |
| 2 | **SSML Prompt Creation** | No advanced TTS/voice config | P0 |
| 3 | **Instance Lifecycle** | No automated setup/teardown | P1 |
| 4 | **Campaign Onboarding** | No enablement automation | P1 |
| 5 | **Workflow Coordination** | Multi-step ops fail atomically | P1 |

### Direct Tools Added (boto3)

| # | Category | Tools Added | Total in Category |
|---|----------|-------------|-------------------|
| 1 | Phone Numbers | 4 | 11 total |
| 2 | Prompts | 6 | 8 total |
| 3 | Contact Flows | 3 | 12 total |
| 4 | Queues | 3 | 9 total |
| 5 | Hours | 3 | 7 total |
| 6 | Routing | 3 | 8 total |
| 7 | Users | 3 | 10 total |
| 8 | Status | 2 | 5 total |
| 9 | Contacts | 3 | 14 total |
| 10 | Recording | 2 | 6 total |
| 11 | Analytics | 3 | 8 total |
| 12 | Cases | 3 | 11 total |
| 13 | AI | 3 | 8 total |

**Total Direct Tools Added**: 41 tools
**Total Lambda Bridge Tools**: 12 tools
**Grand Total**: 107+ tools

---

## Infrastructure Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AWS CLOUD                                     │
│                                                                      │
│  ┌─────────────────┐                                                 │
│  │  API Gateway    │                                                 │
│  │  ────────────   │                                                 │
│  │  /bridge/       │                                                 │
│  │    instance     │                                                 │
│  │    prompt       │   ┌─────────────────┐                           │
│  │    workflow     │──▶│ Lambda Bridge   │                           │
│  └─────────────────┘   │ ─────────────── │                           │
│   ▲                    │ • IAM Coord     │                           │
│   │                    │ • S3 Upload     │                           │
│   │                    │ • Step Functions│                           │
│   │                    └────────┬────────┘                           │
│   │                             │                                    │
│   │    ┌──────────────────────┼────────────────────┐                │
│   │    │                      │                    │                │
│   │    ▼                      ▼                    ▼                │
│   │  ┌─────────┐         ┌─────────┐        ┌────────┐         │
│   │  │ Amazon  │         │   S3    │        │ Dynamo │         │
│   │  │ Connect │         │ Bucket  │        │  DB    │         │
│   │  └────┬────┘         └─────────┘        └────────┘         │
│   │       │                                                     │
│   │       │ Direct APIs                                      │
│   └───────┼───────────────────────────────────────────────────┘
│           │
│           ▼
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                   MCP Server Process                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │
│  │  │ Direct      │  │ Direct      │  │ Lambda          │   │   │
│  │  │ Tools (boto3)│  │ Tools (boto3)│  │ Bridge Client   │ ────┘
│  │  └─────────────┘  └─────────────┘  └─────────────────┘
│  │         │                      │                      │
│  │         ▼                      ▼                      │
│  │  ┌─────────────┐        ┌─────────────┐            │
│  │  │ AWS SDK     │        │ AWS SDK     │            │
│  │  │ ─────────── │        │ ─────────── │            │
│  │  │ • connect   │        │ • profiles  │            │
│  │  │ • cases     │        │ • campaigns │            │
│  │  │ • qconnect  │        │ • analytics │            │
│  │  └─────────────┘        └─────────────┘            │
│  └───────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

---

## Comparison: Community vs Our Implementation

| Feature | Community (85 tools) | Our (107 tools) | Delta |
|---------|---------------------|-----------------|-------|
| **Instance Setup** | Manual | Automated | +5 tools |
| **Phone Numbers** | List only | Full CRUD | +8 tools |
| **Prompts** | None | Full | +8 tools |
| **Contact Flows** | Basic | Templated | +5 tools |
| **Queues** | Basic | Full | +3 tools |
| **Hours** | Basic | Full | +3 tools |
| **Routing** | Basic | Full | +3 tools |
| **Users** | Basic | Full | +3 tools |
| **Agent Status** | List only | Full | +2 tools |
| **Contacts** | Basic | Full | +3 tools |
| **Recording** | Start/Stop | Full | +2 tools |
| **Campaigns** | Basic | +Onboarding | +2 tools |
| **Cases** | Basic | Full | +3 tools |
| **AI/QConnect** | Basic | Full | +3 tools |
| **Analytics** | Minimal | Full | +3 tools |
| **Utilities** | None | Validation helpers | +5 tools |

**Net New Tools: 47**
**Total Target Tools: 107**

---

## Priority Implementation Order

### Phase 1 (Foundation): 25 tools
1. Instance management (5)
2. Phone numbers (5)
3. Prompt management (5)
4. Basic flows (5)
5. Utility tools (5)

### Phase 2 (Configuration): 41 tools
1. Queues, Hours, Routing (15)
2. Users, Status (10)
3. Campaigns (8)
4. Cases (8)

### Phase 3 (Operations): 25 tools
1. Contacts, Recording (10)
2. AI, Analytics (10)
3. Integration polish (5)

### Phase 4 (Advanced): 16 tools
1. Lambda bridge workflows
2. Template engine
3. Multi-region support
4. Disaster recovery

---

## Notes

- **Lambda Bridge Threshold**: Tools requiring >1 AWS service coordination
- **Terraform Threshold**: Static infrastructure (instances, IAM roles)
- **Direct Tool Standard**: Single AWS SDK call with boto3
- **API Coverage**: ~95% of Amazon Connect API surface area