# Amazon Connect MCP Server - API Reference

Complete reference for all MCP tools provided by the Amazon Connect MCP Server.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Contact Flow Tools](#contact-flow-tools)
- [Phone Number Tools](#phone-number-tools)
- [Instance Tools](#instance-tools)
- [Queue Tools](#queue-tools)
- [Hours of Operation Tools](#hours-of-operation-tools)
- [Prompt Tools](#prompt-tools)
- [Response Schemas](#response-schemas)
- [Error Codes](#error-codes)

## Quick Reference

### Tool Categories

| Category | Tool Count | Description |
|:---------|:-----------|:------------|
| Contact Flows | 12 | Flow creation, management, templates |
| Phone Numbers | 6 | Search, claim, release |
| Instances | 5 | Instance configuration |
| Queues | 5 | Queue management |
| Hours of Operation | 8 | Business hours, overrides |
| Prompts | 4 | Audio prompt management |

### Common Parameters

All tools accept these standard parameters:

| Parameter | Type | Required | Description |
|:----------|:-----|:---------|:------------|
| `instance_id` | string | Yes* | Connect instance ID |

*Required for most operations

## Contact Flow Tools

### `contact_flows_list`

List all contact flows in a Connect instance.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `contact_flow_types` | list | No | Filter by types (CONTACT_FLOW, OUTBOUND_WHISPER_FLOW, etc.) |
| `max_results` | integer | No | Maximum results (default: 100) |

**Example:**
```json
{
  "instance_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "contact_flow_types": ["OUTBOUND_WHISPER_FLOW"],
  "max_results": 50
}
```

**Response:**
```json
{
  "status": "success",
  "contact_flows": [
    {
      "id": "flow-id",
      "arn": "arn:aws:connect:.../contact-flow/flow-id",
      "name": "My Flow",
      "type": "OUTBOUND_WHISPER_FLOW",
      "description": "",
      "state": "ACTIVE",
      "last_modified_time": "2024-01-15T10:30:00Z",
      "last_modified_region": "us-east-1"
    }
  ],
  "next_token": null
}
```

### `contact_flows_describe`

Get detailed information about a contact flow including its content.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `contact_flow_id` | string | Yes | Contact flow ID |

**Response:**
```json
{
  "status": "success",
  "contact_flow": {
    "id": "flow-id",
    "arn": "arn:aws:connect:.../contact-flow/flow-id",
    "name": "My Flow",
    "type": "OUTBOUND_WHISPER_FLOW",
    "description": "Description",
    "state": "ACTIVE",
    "created_time": "2024-01-10T08:00:00Z",
    "last_modified_time": "2024-01-15T10:30:00Z",
    "content": { /* Flow JSON */ },
    "tags": {}
  }
}
```

### `contact_flows_create`

Create a new contact flow from raw JSON content.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `name` | string | Yes | Flow name |
| `content` | string | Yes | JSON flow definition as string |
| `type` | string | Yes | Flow type (default: CONTACT_FLOW) |
| `description` | string | No | Flow description |
| `tags` | dict | No | Tags for the flow |

**Example:**
```json
{
  "instance_id": "a1b2c3d4-...",
  "name": "My Flow",
  "content": "{\"Version\":\"2019-10-30\",\"StartAction\":\"PlayPrompt\",...}",
  "type": "OUTBOUND_WHISPER_FLOW",
  "description": "My custom flow",
  "tags": {"Team": "Support"}
}
```

### `contact_flows_create_outbound`

Create an outbound contact flow using a template.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `name` | string | Yes | Flow name |
| `mode` | string | Yes | Template mode: PLAY_PROMPT or AI_AGENT |
| `parameters` | dict | Yes | Template-specific parameters |
| `description` | string | No | Flow description |
| `tags` | dict | No | Flow tags |

**PLAY_PROMPT Mode Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `prompt_text` | string | Yes | TTS message to play |
| `prompt_ssml` | string | No | SSML version of message |
| `campaign_id` | string | No | Campaign identifier |

**AI_AGENT Mode Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `greeting_message` | string | Yes | Initial greeting |
| `greeting_ssml` | string | No | SSML version of greeting |
| `confirmation_question` | string | Yes | Question to ask |
| `confirmation_reply` | string | Yes | Response on confirmation |
| `lex_bot_arn` | string | Yes | Lex bot ARN |
| `lambda_arn` | string | Yes | Lambda function ARN |
| `wait_timeout` | integer | No | Wait seconds (default: 5, min: 1, max: 30) |
| `call_result` | string | No | SUCCESS, NO_ANSWER, BUSY, FAILED |
| `callback_needed` | boolean | No | Callback requested flag |

### `contact_flows_update_content`

Update the content of an existing contact flow.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `contact_flow_id` | string | Yes | Contact flow ID |
| `content` | string | Yes | New JSON flow content |

### `contact_flows_update_from_template`

Update a contact flow using a template.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `contact_flow_id` | string | Yes | Contact flow ID |
| `template_name` | string | Yes | Template to use |
| `parameters` | dict | Yes | Template parameters |

### `contact_flows_delete`

Delete a contact flow.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `contact_flow_id` | string | Yes | Contact flow ID |

### `contact_flows_create_version`

Create a new version of a contact flow.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `contact_flow_id` | string | Yes | Contact flow ID |
| `name` | string | No | Version name |
| `description` | string | No | Version description |

### `contact_flows_search`

Search contact flows with filters.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `search_filter` | dict | No | Filter criteria |
| `max_results` | integer | No | Maximum results |

**Search Filter Options:**

| Filter | Type | Description |
|:-------|:-----|:------------|
| `name_prefix` | string | Match name starting with |
| `contact_flow_types` | list | Filter by types |
| `states` | list | Filter by states (ACTIVE, ARCHIVED) |

### `contact_flows_list_templates`

List available contact flow templates.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `category` | string | No | Filter by category (outbound, inbound, shared) |

### `contact_flows_get_template_schema`

Get the JSON schema for template parameters.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `template_name` | string | Yes | Template name |

### `contact_flows_validate_parameters`

Validate parameters against a template schema.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `template_name` | string | Yes | Template name |
| `parameters` | dict | Yes | Parameters to validate |

## Phone Number Tools

### `connect_phone_numbers_search`

Search for available phone numbers to claim.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `phone_number_country_code` | string | Yes | ISO country code (US, UK, etc.) |
| `phone_number_type` | string | Yes | DID or TOLL_FREE |
| `target_arn` | string | No | Target ARN for the number |
| `prefix` | string | No | Phone number prefix filter |
| `max_results` | integer | No | Maximum results (default: 50) |

**Example:**
```json
{
  "phone_number_country_code": "US",
  "phone_number_type": "TOLL_FREE",
  "max_results": 10
}
```

### `connect_phone_numbers_claim`

Claim a phone number for a Connect instance.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `phone_number` | string | No* | Specific number to claim |
| `country_code` | string | No* | For auto-claim: country code |
| `phone_type` | string | No* | For auto-claim: type |
| `target_arn` | string | No | Where to assign the number |
| `description` | string | No | Number description |

*Either phone_number or (country_code + phone_type) required

### `connect_phone_numbers_release`

Release a previously claimed phone number.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `phone_number_id` | string | Yes | Phone number ID |

### `connect_phone_numbers_list`

List all claimed phone numbers.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `max_results` | integer | No | Maximum results (default: 50) |
| `country_codes` | list | No | Filter by country codes |
| `phone_types` | list | No | Filter by types (DID, TOLL_FREE) |

### `connect_phone_numbers_describe`

Get detailed information about a phone number.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `phone_number_id` | string | Yes | Phone number ID |

### `connect_phone_numbers_update`

Update phone number configuration.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `phone_number_id` | string | Yes | Phone number ID |
| `description` | string | No | New description |
| `target_arn` | string | No | New target assignment |

## Instance Tools

### `connect_instances_list`

List all Connect instances in the AWS account.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `max_results` | integer | No | Maximum results (default: 50) |

### `connect_instances_describe`

Get detailed information about a Connect instance.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |

**Response:**
```json
{
  "instance_id": "...",
  "arn": "arn:aws:connect:...",
  "alias": "my-instance",
  "status": "ACTIVE",
  "inbound_calls_enabled": true,
  "outbound_calls_enabled": true,
  "region": "us-east-1",
  "quota_usage": {
    "claimed_numbers": 3,
    "limit": 100
  }
}
```

### `connect_instances_update`

Update Connect instance settings.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `inbound_calls_enabled` | boolean | No | Enable/disable inbound calls |
| `outbound_calls_enabled` | boolean | No | Enable/disable outbound calls |
| `contact_flow_logs_enabled` | boolean | No | Enable/disable flow logs |
| `contact_lens_enabled` | boolean | No | Enable/disable Contact Lens |

### `connect_instances_create`

Create a new Connect instance (requires Lambda bridge).

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_alias` | string | Yes | Instance alias/name |
| `region` | string | No | AWS region |
| `inbound_calls_enabled` | boolean | No | Enable inbound calls |
| `outbound_calls_enabled` | boolean | No | Enable outbound calls |

### `connect_instances_delete`

Delete a Connect instance (requires Lambda bridge).

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |

## Queue Tools

### `connect_queues_list`

List all queues for an instance.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `queue_types` | list | No | Filter by types (STANDARD, AGENT) |
| `max_results` | integer | No | Maximum results (default: 50) |

### `connect_queues_describe`

Get detailed information about a queue.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `queue_id` | string | Yes | Queue ID |

### `connect_queues_create`

Create a new queue.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `name` | string | Yes | Queue name |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |
| `description` | string | No | Queue description |
| `max_contacts` | integer | No | Maximum contacts limit |
| `quick_connect_ids` | list | No | Associated quick connects |

### `connect_queues_update`

Update an existing queue.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `queue_id` | string | Yes | Queue ID |
| `name` | string | No | New name |
| `description` | string | No | New description |
| `hours_of_operation_id` | string | No | New hours ID |
| `max_contacts` | integer | No | New max contacts |
| `status` | string | No | ENABLED or DISABLED |
| `quick_connect_ids` | list | No | New quick connects |
| `outbound_caller_config` | dict | No | Outbound caller ID config |

### `connect_queues_delete`

Delete a queue.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `queue_id` | string | Yes | Queue ID |

## Hours of Operation Tools

### `connect_hours_of_operations_list`

List hours of operation configurations.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `max_results` | integer | No | Maximum results (default: 50) |

### `connect_hours_of_operations_describe`

Get detailed information about hours of operation.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |

### `connect_hours_of_operations_create`

Create hours of operation.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `name` | string | Yes | Schedule name |
| `time_zone` | string | Yes | Time zone (America/New_York, UTC) |
| `config` | list | Yes | Day/time configurations |
| `description` | string | No | Schedule description |

**Config Format:**
```json
[
  {
    "Day": "MONDAY",
    "StartTime": {"Hours": 9, "Minutes": 0},
    "EndTime": {"Hours": 17, "Minutes": 0}
  }
]
```

### `connect_hours_of_operations_update`

Update hours of operation.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |
| `name` | string | No | New name |
| `description` | string | No | New description |
| `time_zone` | string | No | New time zone |
| `config` | list | No | New configuration |

### `connect_hours_of_operations_delete`

Delete hours of operation.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |

### `connect_hours_of_operations_create_override`

Create an hours of operation override (holiday).

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |
| `name` | string | Yes | Override name |
| `description` | string | No | Override description |
| `start_time` | string | Yes | ISO 8601 start time |
| `end_time` | string | Yes | ISO 8601 end time |

### `connect_hours_of_operations_delete_override`

Delete an hours of operation override.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |
| `override_id` | string | Yes | Override ID |

### `connect_hours_of_operations_describe_override`

Get details about a specific override.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |
| `override_id` | string | Yes | Override ID |

### `connect_hours_of_operations_list_overrides`

List all overrides for hours of operation.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `hours_of_operation_id` | string | Yes | Hours of operation ID |
| `max_results` | integer | No | Maximum results (default: 50) |

## Prompt Tools

### `connect_prompts_list`

List all custom prompts for an instance.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `max_results` | integer | No | Maximum results (default: 50) |

### `connect_prompts_describe`

Get detailed information about a prompt.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `prompt_id` | string | Yes | Prompt ID |

### `connect_prompts_create`

Create a new custom prompt from an S3 audio file.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `name` | string | Yes | Prompt name |
| `s3_uri` | string | Yes | S3 URI to audio file |
| `description` | string | No | Prompt description |

**Audio Requirements:**
- Format: WAV
- Sample rate: 8kHz or 16kHz
- Channels: Mono
- S3 bucket must grant Connect access

### `connect_prompts_delete`

Delete a custom prompt.

**Parameters:**

| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `instance_id` | string | Yes | Connect instance ID |
| `prompt_id` | string | Yes | Prompt ID |

## Response Schemas

### Success Response

All successful tool calls return a response with this structure:

```json
{
  "status": "success",
  "...": "resource-specific fields"
}
```

### Error Response

Failed tool calls return:

```json
{
  "status": "error",
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

## Error Codes

| Code | Description | Resolution |
|:-----|:------------|:-----------|
| `INVALID_PARAMETER` | Invalid parameter value | Check parameter requirements |
| `MISSING_PARAMETER` | Required parameter missing | Provide all required parameters |
| `RESOURCE_NOT_FOUND` | Resource does not exist | Verify resource IDs |
| `RESOURCE_EXISTS` | Resource already exists | Use unique names |
| `PERMISSION_DENIED` | Insufficient permissions | Check IAM policies |
| `RATE_LIMITED` | AWS API rate limit exceeded | Retry with exponential backoff |
| `INTERNAL_ERROR` | Internal server error | Check logs and retry |
| `TEMPLATE_ERROR` | Template processing error | Verify template parameters |
| `VALIDATION_ERROR` | Parameter validation failed | Check parameter schema |
| `BRIDGE_NOT_CONFIGURED` | Lambda bridge not configured | Set CONNECT_API_BRIDGE_URL |
| `API_ERROR` | AWS API error | Check AWS service status |

### Common HTTP Status Codes

When using API Gateway Lambda bridge:

| Status | Meaning |
|:-------|:--------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (IAM/auth issue) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 429 | Rate limited |
| 500 | Internal server error |
| 502 | Lambda execution error |
| 503 | Service unavailable |

## Data Types

### Phone Number Types

| Type | Description |
|:-----|:------------|
| `DID` | Direct Inward Dialing (local number) |
| `TOLL_FREE` | Toll-free number (e.g., 800, 888) |

### Contact Flow Types

| Type | Description |
|:-----|:------------|
| `CONTACT_FLOW` | Inbound contact flow |
| `OUTBOUND_WHISPER_FLOW` | Outbound contact flow |
| `AGENT_WHISPER_FLOW` | Agent greeting flow |
| `AGENT_TRANSFER_FLOW` | Transfer routing flow |
| `QUEUE_TRANSFER_FLOW` | Queue transfer flow |
| `ERROR_FLOW` | Error handling flow |

### Queue Types

| Type | Description |
|:-----|:------------|
| `STANDARD` | Standard queue |
| `AGENT` | Agent-specific queue |

### Days of Week

- SUNDAY
- MONDAY
- TUESDAY
- WEDNESDAY
- THURSDAY
- FRIDAY
- SATURDAY

## Best Practices

1. **Always validate before creating flows**:
   - Use `contact_flows_validate_parameters`
   - Check `contact_flows_get_template_schema`

2. **Handle rate limiting**:
   - Implement exponential backoff
   - Check error response codes

3. **Use appropriate defaults**:
   - Many parameters have sensible defaults
   - Only override when necessary

4. **Tag your resources**:
   - Use tags for organization
   - Enable cost tracking

5. **Test in development**:
   - Use separate instances
   - Validate all changes

6. **Monitor usage**:
   - Watch quota usage
   - Set up CloudWatch alarms
