#!/usr/bin/env python3
"""
Basic Outbound Call Example
===========================

This example demonstrates how to make a simple outbound call using the
Amazon Connect MCP Server.

Prerequisites:
- AWS credentials configured
- Amazon Connect instance with outbound calling enabled
- Connect instance ID

Usage:
    AWS_REGION=us-east-1 \
    CONNECT_INSTANCE_ID=your-instance-id \
    python basic_outbound_call.py
"""

import os
import asyncio
import json

# Required environment variables
REQUIRED_ENV_VARS = [
    "AWS_REGION",
    "CONNECT_INSTANCE_ID",
]


def check_environment():
    """Verify required environment variables are set."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print("Error: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nSet them before running this script:")
        print('export AWS_REGION=us-east-1')
        print('export CONNECT_INSTANCE_ID=your-instance-id')
        return False
    return True


async def example_1_place_outbound_call():
    """Example 1: Place a simple outbound voice contact."""
    print("\n" + "="*60)
    print("Example 1: Place Outbound Call")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    # This assumes you have an MCP client set up
    # In practice, you'd use the MCP client to call the tool
    
    call_params = {
        "instance_id": instance_id,
        "contact_flow_id": "your-contact-flow-id",  # Outbound whisper flow
        "destination_phone_number": "+15551234567",   # Number to call
        "source_phone_number": "+18005550123",        # Your claimed number
        "queue_id": "your-queue-id",                  # Optional queue
        "attributes": {
            "campaign_id": "demo-campaign",
            "customer_id": "CUST-12345",
            "priority": "high"
        }
    }
    
    print("\nCall parameters:")
    print(json.dumps(call_params, indent=2))
    
    print("\nNote: Uncomment the call below after configuring parameters")
    # response = await mcp.call_tool("contacts_start_outbound_voice", call_params)
    # print(f"Call initiated: {response}")


async def example_2_claim_and_associate_number():
    """Example 2: Claim a phone number and associate it with a flow."""
    print("\n" + "="*60)
    print("Example 2: Claim Phone Number")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    # Step 1: Search for available numbers
    print("\nStep 1: Search for available toll-free numbers...")
    search_params = {
        "phone_number_country_code": "US",
        "phone_number_type": "TOLL_FREE",
        "max_results": 5
    }
    
    print("Search parameters:")
    print(json.dumps(search_params, indent=2))
    
    # response = await mcp.call_tool("connect_phone_numbers_search", search_params)
    # phone_number = response["phone_numbers"][0]["phone_number"]
    
    # Step 2: Claim a number
    print("\nStep 2: Claim the phone number...")
    claim_params = {
        "instance_id": instance_id,
        "phone_number": "+1-800-555-0123",  # Replace with actual number
        "description": "Outbound campaign line"
    }
    
    print("Claim parameters:")
    print(json.dumps(claim_params, indent=2))
    
    # response = await mcp.call_tool("connect_phone_numbers_claim", claim_params)
    # phone_number_id = response["phone_number_id"]


async def example_3_list_claimed_numbers():
    """Example 3: List all claimed phone numbers."""
    print("\n" + "="*60)
    print("Example 3: List Claimed Numbers")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    list_params = {
        "instance_id": instance_id,
        "max_results": 50
    }
    
    print("\nList parameters:")
    print(json.dumps(list_params, indent=2))
    
    print("\nNote: Uncomment to execute")
    # response = await mcp.call_tool("connect_phone_numbers_list", list_params)
    # print(json.dumps(response, indent=2))


async def example_4_release_number():
    """Example 4: Release a phone number."""
    print("\n" + "="*60)
    print("Example 4: Release Phone Number")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    # Get the phone number ID from the list
    phone_number_id = "your-phone-number-id"
    
    release_params = {
        "instance_id": instance_id,
        "phone_number_id": phone_number_id
    }
    
    print("\nRelease parameters:")
    print(json.dumps(release_params, indent=2))
    
    print("\nCAUTION: This will release the phone number!")
    print("Uncomment below to execute:")
    # response = await mcp.call_tool("connect_phone_numbers_release", release_params)


async def example_5_check_instance_status():
    """Example 5: Check Connect instance status."""
    print("\n" + "="*60)
    print("Example 5: Check Instance Status")
    print("="*60)
    
    instance_id = os.environ["CONNECT_INSTANCE_ID"]
    
    print("\nChecking instance configuration...")
    
    # response = await mcp.call_tool("connect_instances_describe", {
    #     "instance_id": instance_id
    # })
    # print(json.dumps(response, indent=2))


async def main():
    """Run all examples."""
    print("="*60)
    print("Amazon Connect MCP - Basic Outbound Call Examples")
    print("="*60)
    
    if not check_environment():
        return 1
    
    print("\nEnvironment check passed!")
    print(f"  AWS_REGION: {os.environ.get('AWS_REGION')}")
    print(f"  CONNECT_INSTANCE_ID: {os.environ.get('CONNECT_INSTANCE_ID')}")
    
    try:
        await example_1_place_outbound_call()
        await example_2_claim_and_associate_number()
        await example_3_list_claimed_numbers()
        await example_4_release_number()
        await example_5_check_instance_status()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review the example code")
        print("2. Configure your actual instance and flow IDs")
        print("3. Uncomment the MCP tool calls to execute")
        print("4. Check infrastructure_setup.py for more complex scenarios")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
