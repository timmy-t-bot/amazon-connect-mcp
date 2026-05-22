"""AWS Connect API Lambda Handler.

This Lambda function provides a bridge between API Gateway and AWS Connect APIs
for operations not directly exposed by existing MCP tools.

Supported operations:
- Phone number management (search, claim, release)
- Instance configuration
- Queue management
- Hours of operation
- Prompts/announcements
"""

import json
import boto3
import os
import logging
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
connect_client = boto3.client("connect")
sts_client = boto3.client("sts")


def get_account_id() -> str:
    """Get the current AWS account ID."""
    return sts_client.get_caller_identity()["Account"]


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response object."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        },
        "body": json.dumps(body)
    }


# =============================================================================
# Phone Number Operations
# =============================================================================

def search_available_numbers(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for available phone numbers.
    
    Args:
        PhoneNumberCountryCode: ISO country code (e.g., 'US')
        PhoneNumberType: Type of number (DID, TOLL_FREE)
        TargetArn: ARN of the target (instance or instance:queue)
        PhoneNumberPrefix: Optional prefix filter
        MaxResults: Optional max results (default 50)
    """
    try:
        search_params = {
            "PhoneNumberCountryCode": params["PhoneNumberCountryCode"],
            "PhoneNumberType": params["PhoneNumberType"]
        }
        
        if "PhoneNumberPrefix" in params:
            search_params["PhoneNumberPrefix"] = params["PhoneNumberPrefix"]
        
        if "MaxResults" in params:
            search_params["MaxResults"] = params["MaxResults"]
        
        # Search requires TargetArn
        if "TargetArn" in params:
            search_params["TargetArn"] = params["TargetArn"]
        
        response = connect_client.search_available_phone_numbers(**search_params)
        
        return {
            "status": "success",
            "phone_numbers": [
                {
                    "phone_number": pn.get("PhoneNumber"),
                    "phone_number_country_code": pn.get("PhoneNumberCountryCode"),
                    "phone_number_type": pn.get("PhoneNumberType")
                }
                for pn in response.get("PhoneNumbers", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error searching phone numbers: {str(e)}")
        return {"status": "error", "error": str(e)}


def claim_phone_number(params: Dict[str, Any]) -> Dict[str, Any]:
    """Claim a phone number for the Connect instance.
    
    Args:
        InstanceId: Connect instance ID
        PhoneNumber: The phone number to claim
        TargetArn: ARN where to assign the number
        Description: Optional description
        Tags: Optional tags
    """
    try:
        claim_params = {}
        
        if "InstanceId" in params:
            claim_params["InstanceId"] = params["InstanceId"]
            
        if "TargetArn" in params:
            claim_params["TargetArn"] = params["TargetArn"]
        
        if "PhoneNumber" in params:
            claim_params["PhoneNumber"] = params["PhoneNumber"]
        elif "PhoneNumberCountryCode" in params and "PhoneNumberType" in params:
            # Search and claim automatically
            search_response = search_available_numbers({
                "PhoneNumberCountryCode": params["PhoneNumberCountryCode"],
                "PhoneNumberType": params["PhoneNumberType"],
                "TargetArn": params.get("TargetArn"),
                "MaxResults": 1
            })
            
            if search_response["status"] != "success" or not search_response["phone_numbers"]:
                return {"status": "error", "error": "No available phone numbers found"}
            
            claim_params["PhoneNumber"] = search_response["phone_numbers"][0]["phone_number"]
        
        if "Description" in params:
            claim_params["Description"] = params["Description"]
        
        if "Tags" in params:
            claim_params["Tags"] = params["Tags"]
        
        response = connect_client.claim_phone_number(**claim_params)
        
        return {
            "status": "success",
            "phone_number_id": response.get("PhoneNumberId"),
            "phone_number_arn": response.get("PhoneNumberArn")
        }
    except Exception as e:
        logger.error(f"Error claiming phone number: {str(e)}")
        return {"status": "error", "error": str(e)}


def release_phone_number(params: Dict[str, Any]) -> Dict[str, Any]:
    """Release a phone number from the Connect instance.
    
    Args:
        InstanceId: Connect instance ID
        PhoneNumberId: ID of the phone number to release
    """
    try:
        release_params = {}
        
        if "InstanceId" in params:
            release_params["InstanceId"] = params["InstanceId"]
        
        if "PhoneNumberId" in params:
            release_params["PhoneNumberId"] = params["PhoneNumberId"]
        
        connect_client.release_phone_number(**release_params)
        
        return {
            "status": "success",
            "message": f"Phone number {params.get('PhoneNumberId')} released successfully"
        }
    except Exception as e:
        logger.error(f"Error releasing phone number: {str(e)}")
        return {"status": "error", "error": str(e)}


def list_phone_numbers(params: Dict[str, Any]) -> Dict[str, Any]:
    """List phone numbers for the Connect instance.
    
    Args:
        InstanceId: Connect instance ID
        MaxResults: Optional max results
        PhoneNumberCountryCodes: Optional list of country codes
        PhoneNumberTypes: Optional list of types
    """
    try:
        list_params = {
            "InstanceId": params["InstanceId"]
        }
        
        if "MaxResults" in params:
            list_params["MaxResults"] = params["MaxResults"]
        
        if "PhoneNumberCountryCodes" in params:
            list_params["PhoneNumberCountryCodes"] = params["PhoneNumberCountryCodes"]
        
        if "PhoneNumberTypes" in params:
            list_params["PhoneNumberTypes"] = params["PhoneNumberTypes"]
        
        response = connect_client.list_phone_numbers(**list_params)
        
        return {
            "status": "success",
            "phone_numbers": [
                {
                    "id": pn["Id"],
                    "arn": pn["Arn"],
                    "phone_number": pn["PhoneNumber"],
                    "country_code": pn["PhoneNumberCountryCode"],
                    "type": pn["PhoneNumberType"],
                    "status": pn.get("Status"),
                    "description": pn.get("Description"),
                    "target_arn": pn.get("TargetArn"),
                    "tags": pn.get("Tags", {})
                }
                for pn in response.get("PhoneNumberSummaryList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error listing phone numbers: {str(e)}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Instance Operations
# =============================================================================

def list_instances(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all Connect instances.
    
    Args:
        MaxResults: Optional max results
    """
    try:
        list_params = {}
        
        if "MaxResults" in params:
            list_params["MaxResults"] = params["MaxResults"]
        
        response = connect_client.list_instances(**list_params)
        
        return {
            "status": "success",
            "instances": [
                {
                    "id": inst["Id"],
                    "arn": inst["Arn"],
                    "identity_management_type": inst.get("IdentityManagementType"),
                    "instance_alias": inst.get("InstanceAlias"),
                    "created_time": inst.get("CreatedTime"),
                    "service_role": inst.get("ServiceRole"),
                    "instance_status": inst.get("InstanceStatus"),
                    "status_reason": inst.get("StatusReason"),
                    "inbound_calls_enabled": inst.get("InboundCallsEnabled"),
                    "outbound_calls_enabled": inst.get("OutboundCallsEnabled")
                }
                for inst in response.get("InstanceSummaryList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error listing instances: {str(e)}")
        return {"status": "error", "error": str(e)}


def describe_instance(params: Dict[str, Any]) -> Dict[str, Any]:
    """Describe a Connect instance.
    
    Args:
        InstanceId: Connect instance ID
    """
    try:
        response = connect_client.describe_instance(
            InstanceId=params["InstanceId"]
        )
        
        instance = response.get("Instance", {})
        
        return {
            "status": "success",
            "instance": {
                "id": instance.get("Id"),
                "arn": instance.get("Arn"),
                "identity_management_type": instance.get("IdentityManagementType"),
                "instance_alias": instance.get("InstanceAlias"),
                "created_time": instance.get("CreatedTime"),
                "service_role": instance.get("ServiceRole"),
                "instance_status": instance.get("InstanceStatus"),
                "inbound_calls_enabled": instance.get("InboundCallsEnabled"),
                "outbound_calls_enabled": instance.get("OutboundCallsEnabled")
            }
        }
    except Exception as e:
        logger.error(f"Error describing instance: {str(e)}")
        return {"status": "error", "error": str(e)}


def update_instance(params: Dict[str, Any]) -> Dict[str, Any]:
    """Update a Connect instance.
    
    Args:
        InstanceId: Connect instance ID
        InboundCallsEnabled: Boolean
        OutboundCallsEnabled: Boolean
        ContactFlowLogsEnabled: Optional boolean
        ContactLensAnalyticsEnabled: Optional boolean
    """
    try:
        # Update instance attributes
        attributes = []
        
        if "InboundCallsEnabled" in params:
            attributes.append({
                "AttributeType": "INBOUND_CALLS",
                "Value": str(params["InboundCallsEnabled"]).lower()
            })
        
        if "OutboundCallsEnabled" in params:
            attributes.append({
                "AttributeType": "OUTBOUND_CALLS",
                "Value": str(params["OutboundCallsEnabled"]).lower()
            })
        
        if "ContactFlowLogsEnabled" in params:
            attributes.append({
                "AttributeType": "CONTACT_FLOW_LOGS",
                "Value": str(params["ContactFlowLogsEnabled"]).lower()
            })
        
        if "ContactLensAnalyticsEnabled" in params:
            attributes.append({
                "AttributeType": "CONTACT_LENS_ANALYTICS",
                "Value": str(params["ContactLensAnalyticsEnabled"]).lower()
            })
        
        for attr in attributes:
            connect_client.update_instance_attribute(
                InstanceId=params["InstanceId"],
                AttributeType=attr["AttributeType"],
                Value=attr["Value"]
            )
        
        return {
            "status": "success",
            "message": f"Instance {params['InstanceId']} updated successfully",
            "updated_attributes": [attr["AttributeType"] for attr in attributes]
        }
    except Exception as e:
        logger.error(f"Error updating instance: {str(e)}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Queue Operations
# =============================================================================

def list_queues(params: Dict[str, Any]) -> Dict[str, Any]:
    """List queues for the Connect instance.
    
    Args:
        InstanceId: Connect instance ID
        QueueTypes: Optional list of queue types (STANDARD, AGENT)
        MaxResults: Optional max results
    """
    try:
        list_params = {
            "InstanceId": params["InstanceId"]
        }
        
        if "QueueTypes" in params:
            list_params["QueueTypes"] = params["QueueTypes"]
        
        if "MaxResults" in params:
            list_params["MaxResults"] = params["MaxResults"]
        
        response = connect_client.list_queues(**list_params)
        
        return {
            "status": "success",
            "queues": [
                {
                    "id": q["Id"],
                    "arn": q["Arn"],
                    "name": q["Name"],
                    "type": q.get("QueueType"),
                    "description": q.get("Description"),
                    "status": q.get("Status"),
                    "tags": q.get("Tags", {})
                }
                for q in response.get("QueueSummaryList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error listing queues: {str(e)}")
        return {"status": "error", "error": str(e)}


def describe_queue(params: Dict[str, Any]) -> Dict[str, Any]:
    """Describe a queue.
    
    Args:
        InstanceId: Connect instance ID
        QueueId: Queue ID
    """
    try:
        response = connect_client.describe_queue(
            InstanceId=params["InstanceId"],
            QueueId=params["QueueId"]
        )
        
        queue = response.get("Queue", {})
        
        return {
            "status": "success",
            "queue": {
                "id": queue.get("Id"),
                "arn": queue.get("Arn"),
                "name": queue.get("Name"),
                "description": queue.get("Description"),
                "type": queue.get("QueueType"),
                "status": queue.get("Status"),
                "hours_of_operation_id": queue.get("HoursOfOperationId"),
                "max_contacts": queue.get("MaxContacts"),
                "outbound_caller_config": queue.get("OutboundCallerConfig"),
                "quick_connect_ids": queue.get("QuickConnectIds", []),
                "tags": queue.get("Tags", {})
            }
        }
    except Exception as e:
        logger.error(f"Error describing queue: {str(e)}")
        return {"status": "error", "error": str(e)}


def create_queue(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new queue.
    
    Args:
        InstanceId: Connect instance ID
        Name: Queue name
        Description: Optional description
        HoursOfOperationId: Hours of operation ID
        MaxContacts: Optional max contacts
        QuickConnectIds: Optional list of quick connect IDs
        Tags: Optional tags
    """
    try:
        create_params = {
            "InstanceId": params["InstanceId"],
            "Name": params["Name"],
            "HoursOfOperationId": params["HoursOfOperationId"]
        }
        
        if "Description" in params:
            create_params["Description"] = params["Description"]
        
        if "MaxContacts" in params:
            create_params["MaxContacts"] = params["MaxContacts"]
        
        if "QuickConnectIds" in params:
            create_params["QuickConnectIds"] = params["QuickConnectIds"]
        
        if "Tags" in params:
            create_params["Tags"] = params["Tags"]
        
        response = connect_client.create_queue(**create_params)
        
        return {
            "status": "success",
            "queue_id": response.get("QueueId"),
            "queue_arn": response.get("QueueArn")
        }
    except Exception as e:
        logger.error(f"Error creating queue: {str(e)}")
        return {"status": "error", "error": str(e)}


def update_queue(params: Dict[str, Any]) -> Dict[str, Any]:
    """Update a queue.
    
    Args:
        InstanceId: Connect instance ID
        QueueId: Queue ID
        Name: Optional new name
        Description: Optional description
        HoursOfOperationId: Optional hours of operation ID
        MaxContacts: Optional max contacts
        Status: Optional status
        QuickConnectIds: Optional quick connect IDs
        OutboundCallerConfig: Optional outbound caller configuration
    """
    try:
        update_params = {
            "InstanceId": params["InstanceId"],
            "QueueId": params["QueueId"]
        }
        
        if "HoursOfOperationId" in params:
            update_params["HoursOfOperationId"] = params["HoursOfOperationId"]
        
        if "MaxContacts" in params:
            update_params["MaxContacts"] = params["MaxContacts"]
        
        if "Status" in params:
            update_params["Status"] = params["Status"]
        
        if "Name" in params:
            # Update queue name separately
            connect_client.update_queue_name(
                InstanceId=params["InstanceId"],
                QueueId=params["QueueId"],
                Name=params["Name"]
            )
        
        if "Description" in params:
            # Update queue description separately
            connect_client.update_queue_name(
                InstanceId=params["InstanceId"],
                QueueId=params["QueueId"],
                Description=params["Description"]
            )
        
        if "QuickConnectIds" in params:
            update_params["QuickConnectIds"] = params["QuickConnectIds"]
        
        if "OutboundCallerConfig" in params:
            update_params["OutboundCallerConfig"] = params["OutboundCallerConfig"]
        
        # Call update_queue for remaining params
        if len(update_params) > 2 and "HoursOfOperationId" in update_params:
            connect_client.update_queue(**update_params)
        
        return {
            "status": "success",
            "message": f"Queue {params['QueueId']} updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating queue: {str(e)}")
        return {"status": "error", "error": str(e)}


def delete_queue(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a queue.
    
    Args:
        InstanceId: Connect instance ID
        QueueId: Queue ID
    """
    try:
        connect_client.delete_queue(
            InstanceId=params["InstanceId"],
            QueueId=params["QueueId"]
        )
        
        return {
            "status": "success",
            "message": f"Queue {params['QueueId']} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting queue: {str(e)}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Hours of Operation Operations
# =============================================================================

def list_hours_of_operations(params: Dict[str, Any]) -> Dict[str, Any]:
    """List hours of operations.
    
    Args:
        InstanceId: Connect instance ID
        MaxResults: Optional max results
    """
    try:
        list_params = {
            "InstanceId": params["InstanceId"]
        }
        
        if "MaxResults" in params:
            list_params["MaxResults"] = params["MaxResults"]
        
        response = connect_client.list_hours_of_operations(**list_params)
        
        return {
            "status": "success",
            "hours_of_operations": [
                {
                    "id": hop["Id"],
                    "arn": hop["Arn"],
                    "name": hop["Name"]
                }
                for hop in response.get("HoursOfOperationSummaryList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error listing hours of operations: {str(e)}")
        return {"status": "error", "error": str(e)}


def describe_hours_of_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Describe hours of operation.
    
    Args:
        InstanceId: Connect instance ID
        HoursOfOperationId: Hours of operation ID
    """
    try:
        response = connect_client.describe_hours_of_operation(
            InstanceId=params["InstanceId"],
            HoursOfOperationId=params["HoursOfOperationId"]
        )
        
        hop = response.get("HoursOfOperation", {})
        
        return {
            "status": "success",
            "hours_of_operation": {
                "id": hop.get("Id"),
                "arn": hop.get("Arn"),
                "name": hop.get("Name"),
                "description": hop.get("Description"),
                "time_zone": hop.get("TimeZone"),
                "config": [
                    {
                        "day": c.get("Day"),
                        "start_time": c.get("StartTime"),
                        "end_time": c.get("EndTime")
                    }
                    for c in hop.get("Config", [])
                ],
                "tags": hop.get("Tags", {})
            }
        }
    except Exception as e:
        logger.error(f"Error describing hours of operation: {str(e)}")
        return {"status": "error", "error": str(e)}


def create_hours_of_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create hours of operation.
    
    Args:
        InstanceId: Connect instance ID
        Name: Name for hours
        TimeZone: Time zone (e.g., 'America/New_York')
        Config: List of day/time configs
        Description: Optional description
        Tags: Optional tags
    """
    try:
        create_params = {
            "InstanceId": params["InstanceId"],
            "Name": params["Name"],
            "TimeZone": params["TimeZone"],
            "Config": [
                {
                    "Day": c["Day"],
                    "StartTime": {
                        "Hours": c["StartTime"]["Hours"],
                        "Minutes": c["StartTime"]["Minutes"]
                    },
                    "EndTime": {
                        "Hours": c["EndTime"]["Hours"],
                        "Minutes": c["EndTime"]["Minutes"]
                    }
                }
                for c in params["Config"]
            ]
        }
        
        if "Description" in params:
            create_params["Description"] = params["Description"]
        
        if "Tags" in params:
            create_params["Tags"] = params["Tags"]
        
        response = connect_client.create_hours_of_operation(**create_params)
        
        return {
            "status": "success",
            "hours_of_operation_id": response.get("HoursOfOperationId"),
            "hours_of_operation_arn": response.get("HoursOfOperationArn")
        }
    except Exception as e:
        logger.error(f"Error creating hours of operation: {str(e)}")
        return {"status": "error", "error": str(e)}


def update_hours_of_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Update hours of operation.
    
    Args:
        InstanceId: Connect instance ID
        HoursOfOperationId: Hours of operation ID
        Name: Optional new name
        Description: Optional description
        TimeZone: Optional time zone
        Config: Optional new config
    """
    try:
        # Update name separately
        if "Name" in params:
            connect_client.update_hours_of_operation(
                InstanceId=params["InstanceId"],
                HoursOfOperationId=params["HoursOfOperationId"],
                Name=params["Name"]
            )
        
        # Update time zone separately
        if "TimeZone" in params:
            connect_client.update_hours_of_operation(
                InstanceId=params["InstanceId"],
                HoursOfOperationId=params["HoursOfOperationId"],
                TimeZone=params["TimeZone"]
            )
        
        # Update config separately
        if "Config" in params:
            connect_client.update_hours_of_operation_config(
                InstanceId=params["InstanceId"],
                HoursOfOperationId=params["HoursOfOperationId"],
                Config=[
                    {
                        "Day": c["Day"],
                        "StartTime": {
                            "Hours": c["StartTime"]["Hours"],
                            "Minutes": c["StartTime"]["Minutes"]
                        },
                        "EndTime": {
                            "Hours": c["EndTime"]["Hours"],
                            "Minutes": c["EndTime"]["Minutes"]
                        }
                    }
                    for c in params["Config"]
                ]
            )
        
        return {
            "status": "success",
            "message": f"Hours of operation {params['HoursOfOperationId']} updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating hours of operation: {str(e)}")
        return {"status": "error", "error": str(e)}


def delete_hours_of_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete hours of operation.
    
    Args:
        InstanceId: Connect instance ID
        HoursOfOperationId: Hours of operation ID
    """
    try:
        connect_client.delete_hours_of_operation(
            InstanceId=params["InstanceId"],
            HoursOfOperationId=params["HoursOfOperationId"]
        )
        
        return {
            "status": "success",
            "message": f"Hours of operation {params['HoursOfOperationId']} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting hours of operation: {str(e)}")
        return {"status": "error", "error": str(e)}


def list_hours_of_operation_overrides(params: Dict[str, Any]) -> Dict[str, Any]:
    """List hours of operation overrides.
    
    Args:
        InstanceId: Connect instance ID
        HoursOfOperationId: Hours of operation ID
        MaxResults: Optional max results
    """
    try:
        list_params = {
            "InstanceId": params["InstanceId"],
            "HoursOfOperationId": params["HoursOfOperationId"]
        }
        
        if "MaxResults" in params:
            list_params["MaxResults"] = params["MaxResults"]
        
        response = connect_client.list_hours_of_operation_overrides(**list_params)
        
        return {
            "status": "success",
            "overrides": [
                {
                    "id": o.get("HoursOfOperationOverrideId"),
                    "description": o.get("Description"),
                    "start_time": o.get("StartTime"),
                    "end_time": o.get("EndTime"),
                    "override_config": o.get("OverrideConfig", [])
                }
                for o in response.get("HoursOfOperationOverrideList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error listing hours of operation overrides: {str(e)}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Prompt Operations
# =============================================================================

def list_prompts(params: Dict[str, Any]) -> Dict[str, Any]:
    """List prompts for the Connect instance.
    
    Args:
        InstanceId: Connect instance ID
        MaxResults: Optional max results
    """
    try:
        list_params = {
            "InstanceId": params["InstanceId"]
        }
        
        if "MaxResults" in params:
            list_params["MaxResults"] = params["MaxResults"]
        
        response = connect_client.list_prompts(**list_params)
        
        return {
            "status": "success",
            "prompts": [
                {
                    "id": p["Id"],
                    "arn": p["Arn"],
                    "name": p["Name"]
                }
                for p in response.get("PromptSummaryList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        logger.error(f"Error listing prompts: {str(e)}")
        return {"status": "error", "error": str(e)}


def describe_prompt(params: Dict[str, Any]) -> Dict[str, Any]:
    """Describe a prompt.
    
    Args:
        InstanceId: Connect instance ID
        PromptId: Prompt ID
    """
    try:
        response = connect_client.describe_prompt(
            InstanceId=params["InstanceId"],
            PromptId=params["PromptId"]
        )
        
        prompt = response.get("Prompt", {})
        
        return {
            "status": "success",
            "prompt": {
                "id": prompt.get("Id"),
                "arn": prompt.get("Arn"),
                "name": prompt.get("Name"),
                "description": prompt.get("Description"),
                "s3_uri": prompt.get("S3Uri"),
                "tags": prompt.get("Tags", {})
            }
        }
    except Exception as e:
        logger.error(f"Error describing prompt: {str(e)}")
        return {"status": "error", "error": str(e)}


def create_prompt(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new prompt.
    
    Args:
        InstanceId: Connect instance ID
        Name: Prompt name
        S3Uri: S3 URI for the prompt file
        Description: Optional description
        Tags: Optional tags
    """
    try:
        create_params = {
            "InstanceId": params["InstanceId"],
            "Name": params["Name"],
            "S3Uri": params["S3Uri"]
        }
        
        if "Description" in params:
            create_params["Description"] = params["Description"]
        
        if "Tags" in params:
            create_params["Tags"] = params["Tags"]
        
        response = connect_client.create_prompt(**create_params)
        
        return {
            "status": "success",
            "prompt_arn": response.get("PromptARN"),
            "prompt_id": response.get("PromptId")
        }
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}")
        return {"status": "error", "error": str(e)}


def delete_prompt(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a prompt.
    
    Args:
        InstanceId: Connect instance ID
        PromptId: Prompt ID
    """
    try:
        connect_client.delete_prompt(
            InstanceId=params["InstanceId"],
            PromptId=params["PromptId"]
        )
        
        return {
            "status": "success",
            "message": f"Prompt {params['PromptId']} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting prompt: {str(e)}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Route Handling
# =============================================================================

# Route map for API actions
ROUTE_MAP = {
    # Phone numbers
    "phone-numbers/search": search_available_numbers,
    "phone-numbers/claim": claim_phone_number,
    "phone-numbers/release": release_phone_number,
    "phone-numbers/list": list_phone_numbers,
    
    # Instances
    "instances/list": list_instances,
    "instances/describe": describe_instance,
    "instances/update": update_instance,
    
    # Queues
    "queues/list": list_queues,
    "queues/describe": describe_queue,
    "queues/create": create_queue,
    "queues/update": update_queue,
    "queues/delete": delete_queue,
    
    # Hours of operation
    "hours-of-operations/list": list_hours_of_operations,
    "hours-of-operations/describe": describe_hours_of_operation,
    "hours-of-operations/create": create_hours_of_operation,
    "hours-of-operations/update": update_hours_of_operation,
    "hours-of-operations/delete": delete_hours_of_operation,
    "hours-of-operations/list-overrides": list_hours_of_operation_overrides,
    
    # Prompts
    "prompts/list": list_prompts,
    "prompts/describe": describe_prompt,
    "prompts/create": create_prompt,
    "prompts/delete": delete_prompt,
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler entry point.
    
    Args:
        event: API Gateway event object
        context: Lambda context object
        
    Returns:
        API Gateway response object
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Get path and method from event
        path = event.get("path", "")
        method = event.get("httpMethod", "GET")
        
        # Parse body if present
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError as e:
                return create_response(400, {
                    "status": "error",
                    "message": f"Invalid JSON in request body: {str(e)}"
                })
        
        # Also check query string parameters
        query_params = event.get("queryStringParameters") or {}
        body.update(query_params)
        
        # Extract action from path
        # Path format: /connect/{action}
        path_parts = path.strip("/").split("/")
        
        if len(path_parts) < 2:
            return create_response(400, {
                "status": "error",
                "message": "Invalid path. Expected format: /connect/{action}"
            })
        
        # Support both /connect/{action} and direct /{action} paths
        action_index = 1 if path_parts[0] == "connect" else 0
        action = "/".join(path_parts[action_index:])
        
        # Handle OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            return create_response(200, {"status": "success"})
        
        # Get handler for action
        handler = ROUTE_MAP.get(action)
        
        if not handler:
            available_routes = list(ROUTE_MAP.keys())
            return create_response(404, {
                "status": "error",
                "message": f"Unknown action: {action}",
                "available_routes": available_routes
            })
        
        # Execute handler
        result = handler(body)
        
        # Determine status code
        if result.get("status") == "error":
            status_code = 500
            if "not found" in result.get("error", "").lower():
                status_code = 404
        else:
            status_code = 200
        
        return create_response(status_code, result)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_response(500, {
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        })
