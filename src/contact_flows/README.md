# Contact Flow Builder for Amazon Connect

This module provides parameterized contact flow templates and MCP tools for creating, managing, and updating contact flows in Amazon Connect.

## Features

### Supported Flow Types

1. **Outbound Play Prompt** (`play_prompt_outbound`)
   - Simple TTS message playback
   - No user interaction
   - Configurable SSML support
   - Campaign ID tracking

2. **AI Agent Outbound** (`ai_agent_outbound`)
   - Interactive flow with GetUserInput
   - Amazon Lex integration for intent recognition
   - Lambda function invocation for processing
   - Contact attribute updates
   - Configurable wait timeouts

3. **Appointment Reminder** (`appointment_reminder`)
   - Appointment time announcement
   - Confirmation handling via Lex
   - Lambda processing for rescheduling
   - Result tracking attributes

4. **Payment Reminder** (`payment_reminder`)
   - Balance notification
   - Payment acceptance via Lex
   - Lambda integration for processing
   - Status tracking

5. **Basic IVR** (`basic_ivr`)
   - Hours of operation checking
   - Menu prompts with Lex
   - Queue transfer capability
   - After-hours message handling

## Usage

### MCP Tools

#### Create Outbound Flow

```python
contact_flows_create_outbound(
    instance_id="your-instance-id",
    name="My Outbound Flow",
    mode="PLAY_PROMPT",
    parameters={
        "prompt_text": "Hello, this is an important message from...",
        "campaign_id": "campaign-123"
    }
)

# AI Agent mode
contact_flows_create_outbound(
    instance_id="your-instance-id",
    name="AI Agent Flow",
    mode="AI_AGENT",
    parameters={
        "greeting_message": "Hello! I'm calling on behalf of...",
        "confirmation_question": "Can you confirm your appointment?",
        "confirmation_reply": "Thank you for confirming!",
        "lex_bot_arn": "arn:aws:lex:us-east-1:...:bot-alias/...",
        "lambda_arn": "arn:aws:lambda:us-east-1:...:function:processIntent"
    }
)
```

#### List Contact Flows

```python
contact_flows_list(
    instance_id="your-instance-id",
    contact_flow_types=["OUTBOUND_WHISPER_FLOW", "CONTACT_FLOW"],
    max_results=50
)
```

#### Update Contact Flow

```python
contact_flows_update_content(
    instance_id="your-instance-id",
    contact_flow_id="cf-12345",
    content="{JSON flow content}"
)

# Update using template
contact_flows_update_from_template(
    instance_id="your-instance-id",
    contact_flow_id="cf-12345",
    template_name="ai_agent_outbound",
    parameters={...}
)
```

#### Delete Contact Flow

```python
contact_flows_delete(
    instance_id="your-instance-id",
    contact_flow_id="cf-12345"
)
```

### Template Management

```python
# List available templates
contact_flows_list_templates(category="outbound")

# Get template parameter schema
contact_flows_get_template_schema(template_name="ai_agent_outbound")

# Validate parameters
contact_flows_validate_parameters(
    template_name="ai_agent_outbound",
    parameters={...}
)
```

## Structure

```src/
├── contact_flows/
│   ├── __init__.py
│   └── contact_flow_tools.py    # MCP tools implementation
└── amazon_connect_mcp/
    ├── __init__.py
    └── templates/
        ├── __init__.py
        ├── engine.py              # Template rendering engine
        ├── registry.py            # Template registry
        ├── outbound/
        │   ├── play_prompt_outbound.json
        │   ├── ai_agent_outbound.json
        │   ├── appointment_reminder.json
        │   └── payment_reminder.json
        └── inbound/
            └── basic_ivr.json
```

## Template Syntax

### Variables

Templates use `{{variable_name}}` syntax for parameter substitution.

### Variable Types

- `string` - Text values
- `integer` - Numeric values with min/max constraints
- `boolean` - True/false values
- `arn` - AWS ARN validation
- `enum` - Predefined set of values

### Variable Schema

```json
{
  "Variables": {
    "variable_name": {
      "type": "string",
      "required": true,
      "description": "Human readable description",
      "default": "Default value",
      "min": 1,
      "max": 100,
      "values": ["OPTION_A", "OPTION_B"],
      "ssml_enabled": true
    }
  }
}
```

## Testing

```bash
# Run tests
python -m pytest tests/test_contact_flows.py -v

# Test template rendering
python -c "
from amazon_connect_mcp.templates.engine import TemplateEngine
from amazon_connect_mcp.templates.registry import TemplateRegistry

engine = TemplateEngine()
r = TemplateRegistry()

# List templates
print('Available templates:', r.list_templates())

# Test parameter validation
result = engine.validate_parameters(
    'play_prompt_outbound',
    {'prompt_text': 'Hello World'}
)
print('Validated:', result)

# Render template
rendered = engine.render('play_prompt_outbound', {'prompt_text': 'Test'})
print('Rendered JSON:', json.dumps(rendered, indent=2))
"
```

## Requirements

- boto3 >= 1.28.0
- mcp-server-fastmcp >= 0.1.0
- Python >= 3.8
