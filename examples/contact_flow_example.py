#!/usr/bin/env python3
"""
Contact Flow Examples
=====================

This example demonstrates creating, managing, and using contact flows
with the Amazon Connect MCP Server template engine.

Prerequisites:
- AWS credentials configured
- Amazon Connect instance ID
- Understanding of contact flow templates

Usage:
    AWS_REGION=us-east-1 \
    CONNECT_INSTANCE_ID=your-instance-id \
    python contact_flow_example.py
"""

import os
import asyncio
import json


REQUIRED_ENV_VARS = [
    "AWS_REGION",
    "CONNECT_INSTANCE_ID",
]


def check_environment():
    """Verify required environment variables are set."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        print("Error: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        return False
    return True


async def example_1_list_available_templates():
    """Example 1: List available contact flow templates."""
    print("\n" + "="*60)
    print("Example 1: List Available Templates")
    print("="*60)
    
    print("\nAvailable templates provide pre-built contact flow patterns")
    print("that can be customized with parameters.")
    
    # List all templates
    # response = await mcp.call_tool("contact_flows_list_templates", {})
    
    # List outbound templates only
    # response = await mcp.call_tool("contact_flows_list_templates", {
    #     "category": "outbound"
    # })
    
    example_response = {
        "status": "success",
        "templates": [
            {
                "name": "play_prompt_outbound",
                "version": "2019-10-30",
                "variable_count": 3,
                "description": "Simple outbound message flow"
            },
            {
                "name": "ai_agent_outbound",
                "version": "2019-10-30",
                "variable_count": 9,
                "description": "Interactive AI-powered outbound flow"
            },
            {
                "name": "appointment_reminder",
                "version": "2019-10-30",
                "variable_count": 4,
                "description": "Appointment reminder with confirmation"
            }
        ],
        "count": 3
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_2_get_template_schema():
    """Example 2: Get template parameter schema."""
    print("\n" + "="*60)
    print("Example 2: Get Template Schema")
    print("="*60)
    
    print("\nGet a template's parameter schema before creating a flow:")
    
    # schema = await mcp.call_tool("contact_flows_get_template_schema", {
    #     "template_name": "ai_agent_outbound"
    # })
    
    example_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "ai_agent_outbound Parameters",
        "properties": {
            "greeting_message": {
                "type": "string",
                "description": "Message to play when call connects",
                "ssml_enabled": True
            },
            "wait_timeout": {
                "type": "integer",
                "description": "Seconds to wait for user response",
                "minimum": 1,
                "maximum": 30,
                "default": 5
            },
            "lex_bot_arn": {
                "type": "string",
                "description": "Lex bot ARN for intent recognition"
            },
            "callback_needed": {
                "type": "boolean",
                "description": "Whether a callback was requested",
                "default": False
            }
        },
        "required": ["greeting_message", "confirmation_question", 
                     "lex_bot_arn", "lambda_arn"]
    }
    
    print("\nExample schema (ai_agent_outbound):")
    print(json.dumps(example_schema, indent=2))


async def example_3_validate_template_parameters():
    """Example 3: Validate parameters before creating a flow."""
    print("\n" + "="*60)
    print("Example 3: Validate Template Parameters")
    print("="*60)
    
    print("\nValidate parameters before submission:")
    
    valid_params = {
        "template_name": "play_prompt_outbound",
        "parameters": {
            "prompt_text": "Hello from our service team!",
            "campaign_id": "demo-001"
        }
    }
    
    # response = await mcp.call_tool("contact_flows_validate_parameters", valid_params)
    
    example_response = {
        "status": "success",
        "template_name": "play_prompt_outbound",
        "validated_parameters": {
            "prompt_text": "Hello from our service team!",
            "prompt_ssml": "",  # Default applied
            "campaign_id": "demo-001"
        },
        "message": "Parameters are valid"
    }
    
    print("\nValid parameters example:")
    print(json.dumps(example_response, indent=2))
    
    # Invalid parameters example
    print("\nInvalid parameters example:")
    print(json.dumps({
        "status": "error",
        "error": "Missing required variables: {'prompt_text'}"
    }, indent=2))


async def example_4_create_simple_outbound_flow():
    """Example 4: Create a simple outbound contact flow."""
    print("\n" + "="*60)
    print("Example 4: Create Simple Outbound Flow")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nCreate a simple flow that plays a message and hangs up:\n")
    
    create_params = {
        "instance_id": instance_id,
        "name": "Welcome Message Flow",
        "mode": "PLAY_PROMPT",
        "parameters": {
            "prompt_text": "Hello! Thank you for being a valued customer. "
                          "We hope you're enjoying our services. Goodbye!",
            "campaign_id": "welcome-campaign-001"
        },
        "description": "Simple welcome message for new customers",
        "tags": {
            "Purpose": "Welcome",
            "Team": "Customer Success",
            "Environment": "Production"
        }
    }
    
    print("Create parameters:")
    print(json.dumps(create_params, indent=2))
    
    # response = await mcp.call_tool("contact_flows_create_outbound", create_params)
    
    example_response = {
        "status": "success",
        "contact_flow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "contact_flow_arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/contact-flow/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Welcome Message Flow",
        "type": "OUTBOUND_WHISPER_FLOW",
        "mode": "PLAY_PROMPT",
        "template_used": "play_prompt_outbound",
        "validated_parameters": {
            "prompt_text": "Hello! Thank you...",
            "prompt_ssml": "",
            "campaign_id": "welcome-campaign-001"
        }
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_5_create_interactive_flow():
    """Example 5: Create an interactive AI-powered flow."""
    print("\n" + "="*60)
    print("Example 5: Create Interactive AI Flow")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nCreate an interactive flow with Lex and Lambda:\n")
    
    create_params = {
        "instance_id": instance_id,
        "name": "Customer Feedback Survey",
        "mode": "AI_AGENT",
        "parameters": {
            "greeting_message": "Hello! This is a quick survey about your "
                               "recent experience with our service.",
            "greeting_ssml": "<speak>Hello! <break time='500ms'/> "
                            "This is a quick survey about your recent "
                            "<prosody rate='slow'>experience</prosody> "
                            "with our service.</speak>",
            "confirmation_question": "On a scale of 1 to 5, how satisfied "
                                    "were you with our service?",
            "confirmation_reply": "Thank you for your feedback!",
            "lex_bot_arn": "arn:aws:lex:us-east-1:123456789012:bot:survey-bot",
            "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:process-feedback",
            "wait_timeout": 10,
            "call_result": "SUCCESS",
            "callback_needed": False
        },
        "description": "Interactive customer satisfaction survey",
        "tags": {
            "Purpose": "Survey",
            "Team": "Customer Support",
            "AI": "true"
        }
    }
    
    print("Create parameters:")
    print(json.dumps(create_params, indent=2))
    
    # response = await mcp.call_tool("contact_flows_create_outbound", create_params)
    
    example_response = {
        "status": "success",
        "contact_flow_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
        "contact_flow_arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/contact-flow/b2c3d4e5-f6a7-8901-bcde-f23456789012",
        "name": "Customer Feedback Survey",
        "type": "OUTBOUND_WHISPER_FLOW",
        "mode": "AI_AGENT",
        "template_used": "ai_agent_outbound"
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_6_list_contact_flows():
    """Example 6: List existing contact flows."""
    print("\n" + "="*60)
    print("Example 6: List Contact Flows")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nList all contact flows in the instance:\n")
    
    list_params = {
        "instance_id": instance_id,
        "max_results": 50,
        "contact_flow_types": ["OUTBOUND_WHISPER_FLOW", "CONTACT_FLOW"]
    }
    
    print("List parameters:")
    print(json.dumps(list_params, indent=2))
    
    example_response = {
        "status": "success",
        "contact_flows": [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/contact-flow/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "Welcome Message Flow",
                "type": "OUTBOUND_WHISPER_FLOW",
                "description": "Simple welcome message for new customers",
                "state": "ACTIVE",
                "last_modified_time": "2024-01-15T10:30:00Z"
            },
            {
                "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/contact-flow/b2c3d4e5-f6a7-8901-bcde-f23456789012",
                "name": "Customer Feedback Survey",
                "type": "OUTBOUND_WHISPER_FLOW",
                "description": "Interactive customer satisfaction survey",
                "state": "ACTIVE",
                "last_modified_time": "2024-01-14T09:15:00Z"
            }
        ],
        "next_token": None
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_7_describe_contact_flow():
    """Example 7: Get flow details and content."""
    print("\n" + "="*60)
    print("Example 7: Describe Contact Flow")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nGet complete details about a contact flow:\n")
    
    describe_params = {
        "instance_id": instance_id,
        "contact_flow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
    
    print("Describe parameters:")
    print(json.dumps(describe_params, indent=2))
    
    # response will include flow content and metadata
    
    print("\nExample response includes:")
    print("  - Flow metadata (ID, ARN, name, type)")
    print("  - Flow state (ACTIVE/ARCHIVED)")
    print("  - Created/Modified timestamps")
    print("  - Flow content (JSON actions)")
    print("  - Tags")


async def example_8_update_from_template():
    """Example 8: Update existing flow with new template."""
    print("\n" + "="*60)
    print("Example 8: Update Flow from Template")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nUpdate an existing contact flow with new template parameters:\n")
    
    update_params = {
        "instance_id": instance_id,
        "contact_flow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "template_name": "play_prompt_outbound",
        "parameters": {
            "prompt_text": "Updated message for existing flow!",
            "campaign_id": "updated-campaign-002"
        }
    }
    
    print("Update parameters:")
    print(json.dumps(update_params, indent=2))
    
    # response = await mcp.call_tool("contact_flows_update_from_template", update_params)
    
    example_response = {
        "status": "success",
        "message": "Contact flow a1b2c3d4-e5f6-7890-abcd-ef1234567890 updated from template",
        "template_used": "play_prompt_outbound",
        "validated_parameters": {
            "prompt_text": "Updated message for existing flow!",
            "prompt_ssml": "",
            "campaign_id": "updated-campaign-002"
        }
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_9_create_flow_version():
    """Example 9: Create a flow version."""
    print("\n" + "="*60)
    print("Example 9: Create Flow Version")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nCreate a version of an existing flow:\n")
    
    version_params = {
        "instance_id": instance_id,
        "contact_flow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Version 2.0 - Holiday Update",
        "description": "Updated for holiday campaign"
    }
    
    print("Version parameters:")
    print(json.dumps(version_params, indent=2))
    
    # response = await mcp.call_tool("contact_flows_create_version", version_params)


async def example_10_search_flows():
    """Example 10: Search flows with filters."""
    print("\n" + "="*60)
    print("Example 10: Search Contact Flows")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nSearch flows by name prefix, type, or state:\n")
    
    search_params = {
        "instance_id": instance_id,
        "search_filter": {
            "name_prefix": "Customer",
            "contact_flow_types": ["OUTBOUND_WHISPER_FLOW"],
            "states": ["ACTIVE"]
        },
        "max_results": 20
    }
    
    print("Search parameters:")
    print(json.dumps(search_params, indent=2))
    
    # response = await mcp.call_tool("contact_flows_search", search_params)


async def example_11_delete_flow():
    """Example 11: Delete a contact flow."""
    print("\n" + "="*60)
    print("Example 11: Delete Contact Flow")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nDelete a contact flow:\n")
    
    delete_params = {
        "instance_id": instance_id,
        "contact_flow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
    
    print("Delete parameters:")
    print(json.dumps(delete_params, indent=2))
    
    print("\n⚠️  WARNING: This action cannot be undone!")
    print("Make sure no phone numbers or queues reference this flow.")


async def main():
    """Run all examples."""
    print("="*60)
    print("Amazon Connect MCP - Contact Flow Examples")
    print("="*60)
    
    if not check_environment():
        return 1
    
    print("\nEnvironment check passed!")
    print(f"  AWS_REGION: {os.environ.get('AWS_REGION')}")
    print(f"  CONNECT_INSTANCE_ID: {os.environ.get('CONNECT_INSTANCE_ID')}")
    
    try:
        await example_1_list_available_templates()
        await example_2_get_template_schema()
        await example_3_validate_template_parameters()
        await example_4_create_simple_outbound_flow()
        await example_5_create_interactive_flow()
        await example_6_list_contact_flows()
        await example_7_describe_contact_flow()
        await example_8_update_from_template()
        await example_9_create_flow_version()
        await example_10_search_flows()
        await example_11_delete_flow()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        print("\nKey Learnings:")
        print("1. Templates provide ready-to-use flow patterns")
        print("2. Validate parameters before creating flows")
        print("3. Use mode='PLAY_PROMPT' for simple messages")
        print("4. Use mode='AI_AGENT' for interactive flows")
        print("5. Flows can be updated with new templates")
        print("6. Create versions to track flow changes")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
