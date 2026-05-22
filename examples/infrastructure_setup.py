#!/usr/bin/env python3
"""
Infrastructure Setup Examples
==============================

This example demonstrates setting up Amazon Connect infrastructure
including queues, hours of operation, phone numbers, and prompts.

Prerequisites:
- AWS credentials configured
- Amazon Connect instance ID
- IAM permissions for Connect management

Usage:
    AWS_REGION=us-east-1 \
    CONNECT_INSTANCE_ID=your-instance-id \
    python infrastructure_setup.py
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


async def example_1_list_instances():
    """Example 1: List all Connect instances."""
    print("\n" + "="*60)
    print("Example 1: List Connect Instances")
    print("="*60)
    
    print("\nList all instances in the AWS account:\n")
    
    list_params = {
        "max_results": 50
    }
    
    print("List parameters:")
    print(json.dumps(list_params, indent=2))
    
    example_response = {
        "status": "success",
        "instances": [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "arn": "arn:aws:connect:us-east-1:123456789012:instance/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "identity_management_type": "CONNECT_MANAGED",
                "instance_alias": "my-contact-center",
                "created_time": "2024-01-10T08:00:00Z",
                "service_role": "arn:aws:iam::123456789012:role/service-role/AmazonConnect-MyRole",
                "status": "ACTIVE",
                "inbound_calls_enabled": True,
                "outbound_calls_enabled": True
            }
        ]
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # response = await mcp.call_tool("connect_instances_list", list_params)


async def example_2_describe_instance():
    """Example 2: Get detailed instance information."""
    print("\n" + "="*60)
    print("Example 2: Describe Instance")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nGet detailed information about the instance:\n")
    
    describe_params = {
        "instance_id": instance_id
    }
    
    print("Describe parameters:")
    print(json.dumps(describe_params, indent=2))
    
    # Example response includes instance config, attributes, etc.
    
    print("\nResponse includes:")
    print("  - Instance ID and ARN")
    print("  - Identity management type")
    print("  - Instance alias (custom domain)")
    print("  - Created timestamp")
    print("  - Call capabilities (inbound/outbound)")
    print("  - Storage configuration")
    print("  - Integration status")


async def example_3_update_instance():
    """Example 3: Update instance settings."""
    print("\n" + "="*60)
    print("Example 3: Update Instance Settings")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nEnable or disable instance features:\n")
    
    update_params = {
        "instance_id": instance_id,
        "inbound_calls_enabled": True,
        "outbound_calls_enabled": True,
        "contact_flow_logs_enabled": True,
        "contact_lens_enabled": True
    }
    
    print("Update parameters:")
    print(json.dumps(update_params, indent=2))
    
    # response = await mcp.call_tool("connect_instances_update", update_params)


async def example_4_create_hours_of_operation():
    """Example 4: Create hours of operation."""
    print("\n" + "="*60)
    print("Example 4: Create Hours of Operation")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nCreate business hours schedule for a queue:\n")
    
    create_params = {
        "instance_id": instance_id,
        "name": "Business Hours - Eastern",
        "description": "Standard business hours (9 AM - 5 PM ET)",
        "time_zone": "America/New_York",
        "config": [
            {
                "Day": "MONDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "TUESDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "WEDNESDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "THURSDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "FRIDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            }
        ]
    }
    
    print("Create parameters:")
    print(json.dumps(create_params, indent=2))
    
    # response = await mcp.call_tool("connect_hours_of_operations_create", create_params)
    
    example_response = {
        "status": "success",
        "hours_of_operation_id": "h1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/operating-hours/h1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Business Hours - Eastern"
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_5_list_hours_of_operations():
    """Example 5: List hours of operation configurations."""
    print("\n" + "="*60)
    print("Example 5: List Hours of Operation")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nList all hours of operation configurations:\n")
    
    list_params = {
        "instance_id": instance_id,
        "max_results": 50
    }
    
    print("List parameters:")
    print(json.dumps(list_params, indent=2))
    
    example_response = {
        "status": "success",
        "hours_of_operations": [
            {
                "id": "h1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/operating-hours/h1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "Business Hours - Eastern",
                "time_zone": "America/New_York",
                "config_count": 5
            },
            {
                "id": "h2c3d4e5-f6a7-8901-bcde-f23456789012",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/operating-hours/h2c3d4e5-f6a7-8901-bcde-f23456789012",
                "name": "Extended Hours - Pacific",
                "time_zone": "America/Los_Angeles",
                "config_count": 7
            }
        ]
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # response = await mcp.call_tool("connect_hours_of_operations_list", list_params)


async def example_6_create_queue():
    """Example 6: Create a queue."""
    print("\n" + "="*60)
    print("Example 6: Create Queue")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nCreate a new queue for call routing:\n")
    
    create_params = {
        "instance_id": instance_id,
        "name": "Customer Support Queue",
        "description": "Queue for customer support calls",
        "hours_of_operation_id": "h1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "max_contacts": 100,
        "quick_connect_ids": []  # Optional
    }
    
    print("Create parameters:")
    print(json.dumps(create_params, indent=2))
    
    # response = await mcp.call_tool("connect_queues_create", create_params)
    
    example_response = {
        "status": "success",
        "queue_id": "q1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/queue/q1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))


async def example_7_list_queues():
    """Example 7: List all queues."""
    print("\n" + "="*60)
    print("Example 7: List Queues")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nList all queues:\n")
    
    list_params = {
        "instance_id": instance_id,
        "queue_types": ["STANDARD"],
        "max_results": 50
    }
    
    print("List parameters:")
    print(json.dumps(list_params, indent=2))
    
    example_response = {
        "status": "success",
        "queues": [
            {
                "id": "q1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/queue/q1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "Customer Support Queue",
                "queue_type": "STANDARD",
                "status": "ENABLED"
            },
            {
                "id": "q2c3d4e5-f6a7-8901-bcde-f23456789012",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/queue/q2c3d4e5-f6a7-8901-bcde-f23456789012",
                "name": "Technical Support Queue",
                "queue_type": "STANDARD",
                "status": "ENABLED"
            }
        ]
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # response = await mcp.call_tool("connect_queues_list", list_params)


async def example_8_describe_queue():
    """Example 8: Get detailed queue information."""
    print("\n" + "="*60)
    print("Example 8: Describe Queue")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nGet complete information about a queue:\n")
    
    describe_params = {
        "instance_id": instance_id,
        "queue_id": "q1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
    
    print("Describe parameters:")
    print(json.dumps(describe_params, indent=2))
    
    # Example response includes queue config, status, routing config, etc.
    
    print("\nResponse includes:")
    print("  - Queue ID and ARN")
    print("  - Queue name and description")
    print("  - Status (ENABLED/DISABLED)")
    print("  - Hours of operation ID")
    print("  - Maximum contacts setting")
    print("  - Statistics (if real-time metrics enabled)")


async def example_9_update_queue():
    """Example 9: Update queue configuration."""
    print("\n" + "="*60)
    print("Example 9: Update Queue")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nUpdate queue settings:\n")
    
    update_params = {
        "instance_id": instance_id,
        "queue_id": "q1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Customer Support Queue - Updated",
        "description": "Updated queue for customer support",
        "hours_of_operation_id": "h1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "max_contacts": 150,
        "status": "ENABLED",
        "outbound_caller_config": {
            "outbound_caller_id_name": "Customer Support",
            "outbound_caller_id_number_id": "number-id-here",
            "outbound_flow_id": "flow-id-here"
        }
    }
    
    print("Update parameters:")
    print(json.dumps(update_params, indent=2))
    
    # response = await mcp.call_tool("connect_queues_update", update_params)


async def example_10_search_phone_numbers():
    """Example 10: Search for available phone numbers."""
    print("\n" + "="*60)
    print("Example 10: Search Phone Numbers")
    print("="*60)
    
    print("\nSearch for available numbers to claim:\n")
    
    search_params = {
        "phone_number_country_code": "US",
        "phone_number_type": "TOLL_FREE",
        "max_results": 10
    }
    
    print("Search parameters:")
    print(json.dumps(search_params, indent=2))
    
    example_response = {
        "status": "success",
        "phone_numbers": [
            {
                "phone_number": "+1-800-555-0123",
                "type": "TOLL_FREE",
                "country_code": "US"
            },
            {
                "phone_number": "+1-800-555-0456",
                "type": "TOLL_FREE",
                "country_code": "US"
            },
            {
                "phone_number": "+1-800-555-0789",
                "type": "TOLL_FREE",
                "country_code": "US"
            }
        ]
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # Also show DID search
    print("\nFor DID (local) numbers:")
    did_params = {
        "phone_number_country_code": "US",
        "phone_number_type": "DID",
        "prefix": "+1303555",
        "max_results": 5
    }
    print(json.dumps(did_params, indent=2))
    
    # response = await mcp.call_tool("connect_phone_numbers_search", search_params)


async def example_11_claim_phone_number():
    """Example 11: Claim a phone number."""
    print("\n" + "="*60)
    print("Example 11: Claim Phone Number")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nClaim a specific phone number:\n")
    
    claim_params = {
        "instance_id": instance_id,
        "phone_number": "+1-800-555-0123",
        "description": "Main customer service line",
        "target_arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}:contact-flow/default-outbound-flow"
    }
    
    print("Claim parameters:")
    print(json.dumps(claim_params, indent=2))
    
    example_response = {
        "status": "success",
        "phone_number_id": "p1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:phone-number/p1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "phone_number": "+1-800-555-0123",
        "status": "CLAIMED"
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # response = await mcp.call_tool("connect_phone_numbers_claim", claim_params)


async def example_12_list_claimed_numbers():
    """Example 12: List claimed phone numbers."""
    print("\n" + "="*60)
    print("Example 12: List Claimed Numbers")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nList all claimed phone numbers:\n")
    
    list_params = {
        "instance_id": instance_id,
        "max_results": 50,
        "country_codes": ["US"],
        "phone_types": ["TOLL_FREE", "DID"]
    }
    
    print("List parameters:")
    print(json.dumps(list_params, indent=2))
    
    example_response = {
        "status": "success",
        "phone_numbers": [
            {
                "phone_number_id": "p1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:phone-number/p1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "phone_number": "+1-800-555-0123",
                "country_code": "US",
                "type": "TOLL_FREE",
                "status": "CLAIMED",
                "description": "Main customer service line"
            }
        ]
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # response = await mcp.call_tool("connect_phone_numbers_list", list_params)


async def example_13_create_prompt():
    """Example 13: Create a custom prompt."""
    print("\n" + "="*60)
    print("Example 13: Create Prompt")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nCreate a custom audio prompt from S3:\n")
    
    create_params = {
        "instance_id": instance_id,
        "name": "Welcome Message",
        "s3_uri": "s3://my-connect-prompts/welcome-message.wav",
        "description": "Main welcome message for callers"
    }
    
    print("Create parameters:")
    print(json.dumps(create_params, indent=2))
    
    print("\nNote: Audio files must be:")
    print("  - WAV format")
    print("  - 8kHz or 16kHz sample rate")
    print("  - Mono channel")
    print("  - S3 bucket must allow Connect access")
    
    example_response = {
        "status": "success",
        "prompt_id": "pr1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "arn": f"arn:aws:connect:{os.environ.get('AWS_REGION')}:123456789012:instance/{instance_id}/prompt/pr1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Welcome Message"
    }
    
    print("\nExample response:")
    print(json.dumps(example_response, indent=2))
    
    # response = await mcp.call_tool("connect_prompts_create", create_params)


async def example_14_complete_setup_workflow():
    """Example 14: Complete setup workflow."""
    print("\n" + "="*60)
    print("Example 14: Complete Setup Workflow")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nComplete setup workflow for a new Connect instance:\n")
    
    workflow = {
        "steps": [
            {
                "step": 1,
                "action": "Update instance settings",
                "tool": "connect_instances_update",
                "params": {
                    "outbound_calls_enabled": True,
                    "contact_lens_enabled": True
                }
            },
            {
                "step": 2,
                "action": "Create hours of operation",
                "tool": "connect_hours_of_operations_create",
                "params": {
                    "name": "Business Hours",
                    "time_zone": "America/New_York"
                }
            },
            {
                "step": 3,
                "action": "Create queue",
                "tool": "connect_queues_create",
                "params": {
                    "name": "Main Queue"
                }
            },
            {
                "step": 4,
                "action": "Claim phone number",
                "tool": "connect_phone_numbers_claim",
                "params": {
                    "phone_number": "+1-800-555-0123"
                }
            },
            {
                "step": 5,
                "action": "Create outbound flow",
                "tool": "contact_flows_create_outbound",
                "params": {
                    "name": "Campaign Flow",
                    "mode": "PLAY_PROMPT"
                }
            }
        ]
    }
    
    print("Setup workflow:")
    print(json.dumps(workflow, indent=2))
    
    print("\nEach step depends on previous steps:")
    print("  - Hours ID needed for queue creation")
    print("  - Queue ID needed for routing configuration")
    print("  - Phone number needed for outbound calls")


async def main():
    """Run all examples."""
    print("="*60)
    print("Amazon Connect MCP - Infrastructure Setup Examples")
    print("="*60)
    
    if not check_environment():
        return 1
    
    print("\nEnvironment check passed!")
    print(f"  AWS_REGION: {os.environ.get('AWS_REGION')}")
    print(f"  CONNECT_INSTANCE_ID: {os.environ.get('CONNECT_INSTANCE_ID')}")
    
    try:
        await example_1_list_instances()
        await example_2_describe_instance()
        await example_3_update_instance()
        await example_4_create_hours_of_operation()
        await example_5_list_hours_of_operations()
        await example_6_create_queue()
        await example_7_list_queues()
        await example_8_describe_queue()
        await example_9_update_queue()
        await example_10_search_phone_numbers()
        await example_11_claim_phone_number()
        await example_12_list_claimed_numbers()
        await example_13_create_prompt()
        await example_14_complete_setup_workflow()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        print("\nSetup Summary:")
        print("1. ✓ Configure instance settings")
        print("2. ✓ Create business hours")
        print("3. ✓ Set up queues")
        print("4. ✓ Claim phone numbers")
        print("5. ✓ Create contact flows")
        print("6. ✓ Configure prompts")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
