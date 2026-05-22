"""Amazon Connect MCP Server - Instance Management Tools.

This module provides MCP tools for managing Amazon Connect instances including:
- Creating new instances
- Describing existing instances
- Updating instance settings
- Deleting instances
- Listing all instances
"""

import json
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    STS_AVAILABLE = True
except Exception:
    connect_client = None
    STS_AVAILABLE = False


class ConnectInstanceError(Exception):
    """Exception raised for Connect instance operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_instances_create(
    instance_alias: str,
    identity_management_type: str = "CONNECT_MANAGED",
    directory_id: str = "",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a new Amazon Connect instance.
    
    Args:
        instance_alias: A unique name for the instance
        identity_management_type: Type of identity management - 'CONNECT_MANAGED', 
            'EXISTING_DIRECTORY', or 'SAML'. Defaults to 'CONNECT_MANGED'.
        directory_id: Required when identity_management_type is 'EXISTING_DIRECTORY'.
            The ID of the AWS Directory Service directory.
        tags: Optional dictionary of tags to apply to the instance
        
    Returns:
        Dictionary containing the created instance details including:
        - instance_id: The ID of the new instance
        - instance_arn: The ARN of the new instance
        - instance_alias: The alias/name of the instance
        - status: The creation status
        
    Raises:
        ConnectInstanceError: If the instance creation fails
        
    Example:
        >>> connect_instances_create(
        ...     instance_alias="my-connect-instance",
        ...     identity_management_type="CONNECT_MANAGED",
        ...     tags={"Environment": "Production"}
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "IdentityManagementType": identity_management_type,
            "InstanceAlias": instance_alias
        }
        
        if identity_management_type == "EXISTING_DIRECTORY" and directory_id:
            params["DirectoryId"] = directory_id
        
        if tags:
            params["Tags"] = tags
        
        response = client.create_instance(**params)
        
        return {
            "status": "success",
            "instance_id": response.get("Id"),
            "instance_arn": response.get("Arn"),
            "instance_alias": instance_alias,
            "state": "CREATING"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectInstanceError(f"Failed to create instance: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectInstanceError(f"Failed to create instance: {str(e)}")


def connect_instances_list(
    max_results: int = 50,
    next_token: str = ""
) -> Dict[str, Any]:
    """List all Amazon Connect instances in the AWS account.
    
    Args:
        max_results: Maximum number of results to return (1-10, default 50)
        next_token: Token for pagination from a previous request
        
    Returns:
        Dictionary containing:
        - instances: List of instance summaries with id, arn, alias, status, etc.
        - next_token: Token for fetching the next page of results
        
    Raises:
        ConnectInstanceError: If the API call fails
        
    Example:
        >>> result = connect_instances_list(max_results=10)
        >>> for instance in result["instances"]:
        ...     print(f"{instance['id']}: {instance['instance_alias']}")
    """
    try:
        client = _get_connect_client()
        
        params = {}
        if max_results:
            params["MaxResults"] = max_results
        if next_token:
            params["NextToken"] = next_token
        
        response = client.list_instances(**params)
        
        instances = []
        for inst in response.get("InstanceSummaryList", []):
            instances.append({
                "id": inst.get("Id"),
                "arn": inst.get("Arn"),
                "identity_management_type": inst.get("IdentityManagementType"),
                "instance_alias": inst.get("InstanceAlias"),
                "created_time": inst.get("CreatedTime"),
                "service_role": inst.get("ServiceRole"),
                "instance_status": inst.get("InstanceStatus"),
                "status_reason": inst.get("StatusReason"),
                "inbound_calls_enabled": inst.get("InboundCallsEnabled"),
                "outbound_calls_enabled": inst.get("OutboundCallsEnabled")
            })
        
        return {
            "status": "success",
            "instances": instances,
            "next_token": response.get("NextToken")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectInstanceError(f"Failed to list instances: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectInstanceError(f"Failed to list instances: {str(e)}")


def connect_instances_describe(
    instance_id: str
) -> Dict[str, Any]:
    """Get detailed information about a Connect instance.
    
    Args:
        instance_id: The ID of the Connect instance to describe
        
    Returns:
        Dictionary containing instance details:
        - id: Instance ID
        - arn: Instance ARN
        - identity_management_type: Type of identity management
        - instance_alias: Instance name/alias
        - created_time: When the instance was created
        - service_role: IAM role used by the instance
        - instance_status: Current status (ACTIVE, CREATION_FAILED, etc.)
        - inbound_calls_enabled: Whether inbound calls are enabled
        - outbound_calls_enabled: Whether outbound calls are enabled
        
    Raises:
        ConnectInstanceError: If the instance doesn't exist or API call fails
        
    Example:
        >>> instance = connect_instances_describe(instance_id="12345678-1234-1234-1234-123456789012")
        >>> print(f"Instance {instance['instance_alias']} is {instance['instance_status']}")
    """
    try:
        client = _get_connect_client()
        
        response = client.describe_instance(InstanceId=instance_id)
        
        instance = response.get("Instance", {})
        
        return {
            "status": "success",
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
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectInstanceError(f"Failed to describe instance: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectInstanceError(f"Failed to describe instance: {str(e)}")


def connect_instances_update(
    instance_id: str,
    inbound_calls_enabled: Optional[bool] = None,
    outbound_calls_enabled: Optional[bool] = None,
    contact_flow_logs_enabled: Optional[bool] = None,
    contact_lens_enabled: Optional[bool] = None,
    auto_resolve_best_voices_enabled: Optional[bool] = None,
    early_media_enabled: Optional[bool] = None
) -> Dict[str, Any]:
    """Update Amazon Connect instance settings.
    
    Args:
        instance_id: The ID of the Connect instance
        inbound_calls_enabled: Enable/disable inbound calls
        outbound_calls_enabled: Enable/disable outbound calls
        contact_flow_logs_enabled: Enable/disable contact flow logs
        contact_lens_enabled: Enable/disable Contact Lens analytics
        auto_resolve_best_voices_enabled: Enable/disable auto-resolution of best voices
        early_media_enabled: Enable/disable early media for outbound calls
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the update result
        - updated_attributes: List of attributes that were updated
        
    Raises:
        ConnectInstanceError: If the update fails
        
    Example:
        >>> connect_instances_update(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     inbound_calls_enabled=True,
        ...     outbound_calls_enabled=True
        ... )
    """
    try:
        client = _get_connect_client()
        
        # Map of attribute names to their API types
        attribute_map = {
            "inbound_calls_enabled": "INBOUND_CALLS",
            "outbound_calls_enabled": "OUTBOUND_CALLS",
            "contact_flow_logs_enabled": "CONTACTFLOW_LOGS",
            "contact_lens_enabled": "CONTACT_LENS",
            "auto_resolve_best_voices_enabled": "AUTO_RESOLVE_BEST_VOICES",
            "early_media_enabled": "EARLY_MEDIA"
        }
        
        updated_attributes = []
        errors = []
        
        # Build list of attributes to update
        attributes_to_update = []
        for param_name, api_type in attribute_map.items():
            param_value = locals().get(param_name)
            if param_value is not None:
                attributes_to_update.append({
                    "type": api_type,
                    "value": str(param_value).lower()
                })
        
        # Update each attribute
        for attr in attributes_to_update:
            try:
                client.update_instance_attribute(
                    InstanceId=instance_id,
                    AttributeType=attr["type"],
                    Value=attr["value"]
                )
                updated_attributes.append(attr["type"])
            except ClientError as e:
                errors.append(f"{attr['type']}: {e.response.get('Error', {}).get('Message', str(e))}")
        
        if errors:
            return {
                "status": "partial_success",
                "message": f"Updated {len(updated_attributes)} attributes, {len(errors)} failed",
                "updated_attributes": updated_attributes,
                "errors": errors
            }
        
        return {
            "status": "success",
            "message": f"Instance {instance_id} updated successfully",
            "updated_attributes": updated_attributes
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectInstanceError(f"Failed to update instance: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectInstanceError(f"Failed to update instance: {str(e)}")


def connect_instances_delete(
    instance_id: str
) -> Dict[str, Any]:
    """Delete an Amazon Connect instance.
    
    WARNING: This operation cannot be undone. All data associated with the
    instance will be permanently deleted.
    
    Args:
        instance_id: The ID of the Connect instance to delete
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the deletion result
        
    Raises:
        ConnectInstanceError: If the deletion fails
        
    Example:
        >>> connect_instances_delete(instance_id="12345678-1234-1234-1234-123456789012")
    """
    try:
        client = _get_connect_client()
        
        client.delete_instance(InstanceId=instance_id)
        
        return {
            "status": "success",
            "message": f"Instance {instance_id} deleted successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectInstanceError(f"Failed to delete instance: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectInstanceError(f"Failed to delete instance: {str(e)}")
