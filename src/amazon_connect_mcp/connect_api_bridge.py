"""Amazon Connect MCP Server - Connect API Bridge Tools.

This module provides MCP tools that call Lambda-backed API endpoints
for Connect APIs not directly covered by existing contact flow tools.
"""

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import boto3
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# API Gateway base URL (can be set via environment variable)
API_BASE_URL = os.environ.get("CONNECT_API_BRIDGE_URL", "")


def _get_api_url() -> str:
    """Get the API Gateway base URL."""
    url = os.environ.get("CONNECT_API_BRIDGE_URL", "")
    if not url:
        raise ValueError(
            "CONNECT_API_BRIDGE_URL environment variable must be set. "
            "It should be in the format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}"
        )
    return url.rstrip("/")


def _make_get_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make a GET request to the API Gateway endpoint.
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
        
    Returns:
        Response dictionary
    """
    url = f"{_get_api_url()}/{endpoint}"
    
    if params:
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        if params:
            url = f"{url}?{urlencode(params)}"
    
    # For API Gateway with AWS_IAM auth, we need SigV4 signing
    try:
        if BOTO3_AVAILABLE:
            # Use boto3 to sign the request
            session = boto3.Session()
            credentials = session.get_credentials()
            frozen_credentials = credentials.get_frozen_credentials()
            
            request = AWSRequest(method='GET', url=url)
            SigV4Auth(frozen_credentials, 'execute-api', session.region_name).add_auth(request)
            
            headers = dict(request.headers)
            response = requests.get(url, headers=headers, timeout=30)
        else:
            # Fallback to unsigned request (requires API key or authorizer)
            response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to call {endpoint}"
        }


def _make_post_request(endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Make a POST request to the API Gateway endpoint.
    
    Args:
        endpoint: API endpoint path
        body: Request body
        
    Returns:
        Response dictionary
    """
    url = f"{_get_api_url()}/{endpoint}"
    
    try:
        if BOTO3_AVAILABLE:
            # Use boto3 to sign the request
            session = boto3.Session()
            credentials = session.get_credentials()
            frozen_credentials = credentials.get_frozen_credentials()
            
            request = AWSRequest(method='POST', url=url, data=json.dumps(body))
            request.headers['Content-Type'] = 'application/json'
            SigV4Auth(frozen_credentials, 'execute-api', session.region_name).add_auth(request)
            
            headers = dict(request.headers)
            response = requests.post(url, headers=headers, json=body, timeout=30)
        else:
            # Fallback to unsigned request
            response = requests.post(url, json=body, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to call {endpoint}"
        }


# =============================================================================
# MCP Tool Functions
# =============================================================================

def connect_phone_numbers_search(
    phone_number_country_code: str,
    phone_number_type: str,
    target_arn: str = "",
    prefix: str = "",
    max_results: int = 50
) -> Dict[str, Any]:
    """Search for available phone numbers to claim.
    
    Args:
        phone_number_country_code: ISO country code (e.g., 'US', 'UK', 'CA')
        phone_number_type: Type of number - 'DID' or 'TOLL_FREE'
        target_arn: ARN of target (instance or format: instance:queue)
        prefix: Optional phone number prefix filter
        max_results: Maximum number of results to return (default 50)
        
    Returns:
        Dictionary with available phone numbers
        
    Example:
        {
            "status": "success",
            "phone_numbers": [
                {"phone_number": "+1-800-555-0123", "type": "TOLL_FREE"}
            ]
        }
    """
    params = {
        "PhoneNumberCountryCode": phone_number_country_code,
        "PhoneNumberType": phone_number_type,
        "MaxResults": max_results
    }
    
    if target_arn:
        params["TargetArn"] = target_arn
    if prefix:
        params["PhoneNumberPrefix"] = prefix
    
    return _make_post_request("phone-numbers/search", params)


def connect_phone_numbers_claim(
    instance_id: str,
    phone_number: str = "",
    country_code: str = "",
    phone_type: str = "",
    target_arn: str = "",
    description: str = ""
) -> Dict[str, Any]:
    """Claim a phone number for a Connect instance.
    
    Can either claim a specific number or auto-claim a number.
    
    Args:
        instance_id: Connect instance ID
        phone_number: Specific phone number to claim (e.g., +1-800-555-0123)
        country_code: For auto-claim: country code (e.g., 'US')
        phone_type: For auto-claim: type ('DID' or 'TOLL_FREE')
        target_arn: ARN where to assign the number
        description: Optional description for the phone number
        
    Returns:
        Dictionary with claimed phone number ID and ARN
    """
    params = {
        "InstanceId": instance_id
    }
    
    if phone_number:
        params["PhoneNumber"] = phone_number
    
    if country_code:
        params["PhoneNumberCountryCode"] = country_code
    
    if phone_type:
        params["PhoneNumberType"] = phone_type
    
    if target_arn:
        params["TargetArn"] = target_arn
    
    if description:
        params["Description"] = description
    
    return _make_post_request("phone-numbers/claim", params)


def connect_phone_numbers_release(
    instance_id: str,
    phone_number_id: str
) -> Dict[str, Any]:
    """Release a previously claimed phone number.
    
    Args:
        instance_id: Connect instance ID
        phone_number_id: ID of the phone number to release
        
    Returns:
        Dictionary with release status
    """
    params = {
        "InstanceId": instance_id,
        "PhoneNumberId": phone_number_id
    }
    
    return _make_post_request("phone-numbers/release", params)


def connect_phone_numbers_list(
    instance_id: str,
    max_results: int = 50,
    country_codes: Optional[List[str]] = None,
    phone_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """List all phone numbers for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        max_results: Maximum number of results (default 50)
        country_codes: Optional list of country codes to filter
        phone_types: Optional list of types to filter ('DID', 'TOLL_FREE')
        
    Returns:
        Dictionary with list of claimed phone numbers
    """
    params = {
        "InstanceId": instance_id,
        "MaxResults": max_results
    }
    
    if country_codes:
        params["PhoneNumberCountryCodes"] = country_codes
    
    if phone_types:
        params["PhoneNumberTypes"] = phone_types
    
    return _make_get_request("phone-numbers/list", params)


def connect_instances_list(
    max_results: int = 50
) -> Dict[str, Any]:
    """List all Connect instances in the AWS account.
    
    Args:
        max_results: Maximum number of results (default 50)
        
    Returns:
        Dictionary with list of Connect instances
    """
    params = {
        "MaxResults": max_results
    }
    
    return _make_get_request("instances/list", params)


def connect_instances_describe(
    instance_id: str
) -> Dict[str, Any]:
    """Get detailed information about a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        
    Returns:
        Dictionary with instance details
    """
    params = {
        "InstanceId": instance_id
    }
    
    return _make_get_request("instances/describe", params)


def connect_instances_update(
    instance_id: str,
    inbound_calls_enabled: Optional[bool] = None,
    outbound_calls_enabled: Optional[bool] = None,
    contact_flow_logs_enabled: Optional[bool] = None,
    contact_lens_enabled: Optional[bool] = None
) -> Dict[str, Any]:
    """Update Connect instance settings.
    
    Args:
        instance_id: Connect instance ID
        inbound_calls_enabled: Enable/disable inbound calls
        outbound_calls_enabled: Enable/disable outbound calls
        contact_flow_logs_enabled: Enable/disable contact flow logs
        contact_lens_enabled: Enable/disable Contact Lens Analytics
        
    Returns:
        Dictionary with update status
    """
    params = {
        "InstanceId": instance_id
    }
    
    if inbound_calls_enabled is not None:
        params["InboundCallsEnabled"] = inbound_calls_enabled
    
    if outbound_calls_enabled is not None:
        params["OutboundCallsEnabled"] = outbound_calls_enabled
    
    if contact_flow_logs_enabled is not None:
        params["ContactFlowLogsEnabled"] = contact_flow_logs_enabled
    
    if contact_lens_enabled is not None:
        params["ContactLensAnalyticsEnabled"] = contact_lens_enabled
    
    return _make_post_request("instances/update", params)


def connect_queues_list(
    instance_id: str,
    queue_types: Optional[List[str]] = None,
    max_results: int = 50
) -> Dict[str, Any]:
    """List all queues for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        queue_types: Optional type filter ('STANDARD', 'AGENT')
        max_results: Maximum number of results (default 50)
        
    Returns:
        Dictionary with list of queues
    """
    params = {
        "InstanceId": instance_id,
        "MaxResults": max_results
    }
    
    if queue_types:
        params["QueueTypes"] = queue_types
    
    return _make_get_request("queues/list", params)


def connect_queues_describe(
    instance_id: str,
    queue_id: str
) -> Dict[str, Any]:
    """Get detailed information about a queue.
    
    Args:
        instance_id: Connect instance ID
        queue_id: Queue ID
        
    Returns:
        Dictionary with queue details
    """
    params = {
        "InstanceId": instance_id,
        "QueueId": queue_id
    }
    
    return _make_get_request("queues/describe", params)


def connect_queues_create(
    instance_id: str,
    name: str,
    hours_of_operation_id: str,
    description: str = "",
    max_contacts: Optional[int] = None,
    quick_connect_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a new queue.
    
    Args:
        instance_id: Connect instance ID
        name: Queue name
        hours_of_operation_id: Hours of operation ID
        description: Optional description
        max_contacts: Optional maximum number of contacts
        quick_connect_ids: Optional list of quick connect IDs
        
    Returns:
        Dictionary with created queue ID and ARN
    """
    params = {
        "InstanceId": instance_id,
        "Name": name,
        "HoursOfOperationId": hours_of_operation_id
    }
    
    if description:
        params["Description"] = description
    
    if max_contacts is not None:
        params["MaxContacts"] = max_contacts
    
    if quick_connect_ids:
        params["QuickConnectIds"] = quick_connect_ids
    
    return _make_post_request("queues/create", params)


def connect_queues_update(
    instance_id: str,
    queue_id: str,
    name: str = "",
    description: str = "",
    hours_of_operation_id: str = "",
    max_contacts: Optional[int] = None,
    status: str = "",
    quick_connect_ids: Optional[List[str]] = None,
    outbound_caller_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update an existing queue.
    
    Args:
        instance_id: Connect instance ID
        queue_id: Queue ID
        name: Optional new name
        description: Optional new description
        hours_of_operation_id: Optional new hours of operation ID
        max_contacts: Optional new max contacts limit
        status: Optional new status
        quick_connect_ids: Optional new quick connect IDs
        outbound_caller_config: Optional outbound caller configuration
        
    Returns:
        Dictionary with update status
    """
    params = {
        "InstanceId": instance_id,
        "QueueId": queue_id
    }
    
    if name:
        params["Name"] = name
    
    if description:
        params["Description"] = description
    
    if hours_of_operation_id:
        params["HoursOfOperationId"] = hours_of_operation_id
    
    if max_contacts is not None:
        params["MaxContacts"] = max_contacts
    
    if status:
        params["Status"] = status
    
    if quick_connect_ids is not None:
        params["QuickConnectIds"] = quick_connect_ids
    
    if outbound_caller_config:
        params["OutboundCallerConfig"] = outbound_caller_config
    
    return _make_post_request("queues/update", params)


def connect_queues_delete(
    instance_id: str,
    queue_id: str
) -> Dict[str, Any]:
    """Delete a queue.
    
    Args:
        instance_id: Connect instance ID
        queue_id: Queue ID
        
    Returns:
        Dictionary with deletion status
    """
    params = {
        "InstanceId": instance_id,
        "QueueId": queue_id
    }
    
    return _make_post_request("queues/delete", params)


def connect_hours_of_operations_list(
    instance_id: str,
    max_results: int = 50
) -> Dict[str, Any]:
    """List hours of operation configurations.
    
    Args:
        instance_id: Connect instance ID
        max_results: Maximum number of results (default 50)
        
    Returns:
        Dictionary with list of hours of operations
    """
    params = {
        "InstanceId": instance_id,
        "MaxResults": max_results
    }
    
    return _make_get_request("hours-of-operations/list", params)


def connect_hours_of_operations_describe(
    instance_id: str,
    hours_of_operation_id: str
) -> Dict[str, Any]:
    """Get detailed information about hours of operation.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        
    Returns:
        Dictionary with hours of operation details
    """
    params = {
        "InstanceId": instance_id,
        "HoursOfOperationId": hours_of_operation_id
    }
    
    return _make_get_request("hours-of-operations/describe", params)


def connect_hours_of_operations_create(
    instance_id: str,
    name: str,
    time_zone: str,
    config: List[Dict[str, Any]],
    description: str = ""
) -> Dict[str, Any]:
    """Create hours of operation.
    
    Args:
        instance_id: Connect instance ID
        name: Name for hours of operation
        time_zone: Time zone (e.g., 'America/New_York', 'UTC')
        config: List of day/time configurations
            Each item should have:
            - day: Day of week (SUNDAY, MONDAY, etc.)
            - start_time: Dict with Hours and Minutes
            - end_time: Dict with Hours and Minutes
        description: Optional description
        
    Returns:
        Dictionary with created hours of operation ID and ARN
        
    Example config:
        [
            {
                "Day": "MONDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            }
        ]
    """
    params = {
        "InstanceId": instance_id,
        "Name": name,
        "TimeZone": time_zone,
        "Config": config
    }
    
    if description:
        params["Description"] = description
    
    return _make_post_request("hours-of-operations/create", params)


def connect_hours_of_operations_update(
    instance_id: str,
    hours_of_operation_id: str,
    name: str = "",
    description: str = "",
    time_zone: str = "",
    config: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update hours of operation.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        name: Optional new name
        description: Optional new description
        time_zone: Optional new time zone
        config: Optional new configuration
        
    Returns:
        Dictionary with update status
    """
    params = {
        "InstanceId": instance_id,
        "HoursOfOperationId": hours_of_operation_id
    }
    
    if name:
        params["Name"] = name
    
    if description:
        params["Description"] = description
    
    if time_zone:
        params["TimeZone"] = time_zone
    
    if config is not None:
        params["Config"] = config
    
    return _make_post_request("hours-of-operations/update", params)


def connect_hours_of_operations_delete(
    instance_id: str,
    hours_of_operation_id: str
) -> Dict[str, Any]:
    """Delete hours of operation.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        
    Returns:
        Dictionary with deletion status
    """
    params = {
        "InstanceId": instance_id,
        "HoursOfOperationId": hours_of_operation_id
    }
    
    return _make_post_request("hours-of-operations/delete", params)


def connect_hours_of_operations_list_overrides(
    instance_id: str,
    hours_of_operation_id: str,
    max_results: int = 50
) -> Dict[str, Any]:
    """List hours of operation overrides (holidays, special hours).
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        max_results: Maximum number of results (default 50)
        
    Returns:
        Dictionary with list of overrides
    """
    params = {
        "InstanceId": instance_id,
        "HoursOfOperationId": hours_of_operation_id,
        "MaxResults": max_results
    }
    
    return _make_get_request("hours-of-operations/list-overrides", params)


def connect_prompts_list(
    instance_id: str,
    max_results: int = 50
) -> Dict[str, Any]:
    """List all custom prompts for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        max_results: Maximum number of results (default 50)
        
    Returns:
        Dictionary with list of prompts
    """
    params = {
        "InstanceId": instance_id,
        "MaxResults": max_results
    }
    
    return _make_get_request("prompts/list", params)


def connect_prompts_describe(
    instance_id: str,
    prompt_id: str
) -> Dict[str, Any]:
    """Get detailed information about a prompt.
    
    Args:
        instance_id: Connect instance ID
        prompt_id: Prompt ID
        
    Returns:
        Dictionary with prompt details
    """
    params = {
        "InstanceId": instance_id,
        "PromptId": prompt_id
    }
    
    return _make_get_request("prompts/describe", params)


def connect_prompts_create(
    instance_id: str,
    name: str,
    s3_uri: str,
    description: str = ""
) -> Dict[str, Any]:
    """Create a new custom prompt from an S3 audio file.
    
    Args:
        instance_id: Connect instance ID
        name: Prompt name
        s3_uri: S3 URI to the audio file (WAV format, 8kHz or 16kHz)
        description: Optional description
        
    Returns:
        Dictionary with created prompt ARN and ID
    """
    params = {
        "InstanceId": instance_id,
        "Name": name,
        "S3Uri": s3_uri
    }
    
    if description:
        params["Description"] = description
    
    return _make_post_request("prompts/create", params)


def connect_prompts_delete(
    instance_id: str,
    prompt_id: str
) -> Dict[str, Any]:
    """Delete a custom prompt.
    
    Args:
        instance_id: Connect instance ID
        prompt_id: Prompt ID
        
    Returns:
        Dictionary with deletion status
    """
    params = {
        "InstanceId": instance_id,
        "PromptId": prompt_id
    }
    
    return _make_post_request("prompts/delete", params)


# =============================================================================
# Tool Registration Helper
# =============================================================================

REGISTERED_TOOLS = [
    # Phone Numbers
    connect_phone_numbers_search,
    connect_phone_numbers_claim,
    connect_phone_numbers_release,
    connect_phone_numbers_list,
    
    # Instances
    connect_instances_list,
    connect_instances_describe,
    connect_instances_update,
    
    # Queues
    connect_queues_list,
    connect_queues_describe,
    connect_queues_create,
    connect_queues_update,
    connect_queues_delete,
    
    # Hours of Operation
    connect_hours_of_operations_list,
    connect_hours_of_operations_describe,
    connect_hours_of_operations_create,
    connect_hours_of_operations_update,
    connect_hours_of_operations_delete,
    connect_hours_of_operations_list_overrides,
    
    # Prompts
    connect_prompts_list,
    connect_prompts_describe,
    connect_prompts_create,
    connect_prompts_delete,
]


def register_with_mcp(mcp_server):
    """Register all Connect API bridge tools with an MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    for tool_func in REGISTERED_TOOLS:
        mcp_server.tool()(tool_func)
