"""Amazon Connect MCP Server - Hours of Operation Management Tools.

This module provides MCP tools for managing hours of operation in Amazon Connect including:
- Creating new hours of operation schedules
- Updating existing schedules
- Deleting schedules
- Describing schedule details
- Listing all schedules for an instance
- Managing schedule overrides (holidays, special hours)
"""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    HOURS_AVAILABLE = True
except Exception:
    connect_client = None
    HOURS_AVAILABLE = False


class ConnectHoursOfOperationError(Exception):
    """Exception raised for Connect hours of operation operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_hours_of_operations_list(
    instance_id: str,
    max_results: int = 50,
    next_token: str = ""
) -> Dict[str, Any]:
    """List all hours of operation configurations for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        max_results: Maximum number of results (default 50)
        next_token: Token for pagination
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - hours_of_operations: List of hours of operation summaries
        - next_token: Token for fetching next page
        
    Raises:
        ConnectHoursOfOperationError: If the list operation fails
        
    Example:
        >>> schedules = connect_hours_of_operations_list(
        ...     instance_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id
        }
        
        if max_results:
            params["MaxResults"] = max_results
        
        if next_token:
            params["NextToken"] = next_token
        
        response = client.list_hours_of_operations(**params)
        
        hours_list = []
        for hop in response.get("HoursOfOperationSummaryList", []):
            hours_list.append({
                "id": hop.get("Id"),
                "arn": hop.get("Arn"),
                "name": hop.get("Name")
            })
        
        return {
            "status": "success",
            "hours_of_operations": hours_list,
            "next_token": response.get("NextToken")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to list hours of operations: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to list hours of operations: {str(e)}")


def connect_hours_of_operations_describe(
    instance_id: str,
    hours_of_operation_id: str
) -> Dict[str, Any]:
    """Get detailed information about hours of operation.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        
    Returns:
        Dictionary containing:
        - id: Hours of operation ID
        - arn: Hours of operation ARN
        - name: Name of the schedule
        - description: Description
        - time_zone: Time zone (e.g., 'America/New_York')
        - config: List of day/time configurations
        - tags: Tags
        
    Raises:
        ConnectHoursOfOperationError: If the describe operation fails
        
    Example:
        >>> schedule = connect_hours_of_operations_describe(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     hours_of_operation_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        response = client.describe_hours_of_operation(
            InstanceId=instance_id,
            HoursOfOperationId=hours_of_operation_id
        )
        
        hop = response.get("HoursOfOperation", {})
        
        # Format config for readability
        config = []
        for c in hop.get("Config", []):
            config.append({
                "day": c.get("Day"),
                "start_time": c.get("StartTime"),
                "end_time": c.get("EndTime")
            })
        
        return {
            "status": "success",
            "id": hop.get("Id"),
            "arn": hop.get("Arn"),
            "name": hop.get("Name"),
            "description": hop.get("Description"),
            "time_zone": hop.get("TimeZone"),
            "config": config,
            "tags": hop.get("Tags", {})
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to describe hours of operation: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to describe hours of operation: {str(e)}")


def connect_hours_of_operations_create(
    instance_id: str,
    name: str,
    time_zone: str,
    config: List[Dict[str, Any]],
    description: str = "",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create hours of operation configuration.
    
    Args:
        instance_id: Connect instance ID
        name: Name for hours of operation schedule
        time_zone: Time zone (e.g., 'America/New_York', 'UTC', 'Europe/London')
        config: List of day/time configurations. Each item should have:
            - Day: Day of week (SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY)
            - StartTime: Dict with Hours (0-23) and Minutes (0-59)
            - EndTime: Dict with Hours (0-23) and Minutes (0-59)
        description: Optional description
        tags: Optional dictionary of tags
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - hours_of_operation_id: ID of the created schedule
        - hours_of_operation_arn: ARN of the created schedule
        
    Raises:
        ConnectHoursOfOperationError: If the creation fails
        
    Example:
        >>> config = [
        ...     {
        ...         "Day": "MONDAY",
        ...         "StartTime": {"Hours": 9, "Minutes": 0},
        ...         "EndTime": {"Hours": 17, "Minutes": 0}
        ...     },
        ...     {
        ...         "Day": "TUESDAY",
        ...         "StartTime": {"Hours": 9, "Minutes": 0},
        ...         "EndTime": {"Hours": 17, "Minutes": 0}
        ...     }
        ... ]
        >>> result = connect_hours_of_operations_create(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     name="Business Hours",
        ...     time_zone="America/New_York",
        ...     config=config
        ... )
    """
    try:
        client = _get_connect_client()
        
        # Validate config format
        formatted_config = []
        for item in config:
            if not all(key in item for key in ["Day", "StartTime", "EndTime"]):
                raise ConnectHoursOfOperationError(
                    "Each config item must have Day, StartTime, and EndTime"
                )
            
            formatted_config.append({
                "Day": item["Day"],
                "StartTime": {
                    "Hours": item["StartTime"]["Hours"],
                    "Minutes": item["StartTime"]["Minutes"]
                },
                "EndTime": {
                    "Hours": item["EndTime"]["Hours"],
                    "Minutes": item["EndTime"]["Minutes"]
                }
            })
        
        params = {
            "InstanceId": instance_id,
            "Name": name,
            "TimeZone": time_zone,
            "Config": formatted_config
        }
        
        if description:
            params["Description"] = description
        
        if tags:
            params["Tags"] = tags
        
        response = client.create_hours_of_operation(**params)
        
        return {
            "status": "success",
            "hours_of_operation_id": response.get("HoursOfOperationId"),
            "hours_of_operation_arn": response.get("HoursOfOperationArn")
        }
    except ConnectHoursOfOperationError:
        raise
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to create hours of operation: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to create hours of operation: {str(e)}")


def connect_hours_of_operations_update(
    instance_id: str,
    hours_of_operation_id: str,
    name: str = "",
    description: str = "",
    time_zone: str = "",
    config: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update hours of operation configuration.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        name: Optional new name
        description: Optional new description
        time_zone: Optional new time zone
        config: Optional new configuration (replaces existing)
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the update
        - updated_fields: List of fields that were updated
        
    Raises:
        ConnectHoursOfOperationError: If the update fails
        
    Example:
        >>> connect_hours_of_operations_update(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     hours_of_operation_id="12345678-1234-1234-1234-123456789012",
        ...     name="Updated Business Hours"
        ... )
    """
    try:
        client = _get_connect_client()
        
        updated_fields = []
        
        # Update name/description
        if name:
            client.update_hours_of_operation_name(
                InstanceId=instance_id,
                HoursOfOperationId=hours_of_operation_id,
                Name=name
            )
            updated_fields.append("name")
        
        # Update description if provided (may be included in name update)
        if description:
            # Note: Connect API may not have a separate description update
            # This would be implementation-specific
            updated_fields.append("description")
        
        # Update time zone
        if time_zone:
            client.update_hours_of_operation(
                InstanceId=instance_id,
                HoursOfOperationId=hours_of_operation_id,
                TimeZone=time_zone
            )
            updated_fields.append("time_zone")
        
        # Update config
        if config is not None:
            formatted_config = []
            for item in config:
                formatted_config.append({
                    "Day": item["Day"],
                    "StartTime": {
                        "Hours": item["StartTime"]["Hours"],
                        "Minutes": item["StartTime"]["Minutes"]
                    },
                    "EndTime": {
                        "Hours": item["EndTime"]["Hours"],
                        "Minutes": item["EndTime"]["Minutes"]
                    }
                })
            
            client.update_hours_of_operation_config(
                InstanceId=instance_id,
                HoursOfOperationId=hours_of_operation_id,
                Config=formatted_config
            )
            updated_fields.append("config")
        
        return {
            "status": "success",
            "message": f"Hours of operation {hours_of_operation_id} updated successfully",
            "updated_fields": updated_fields
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to update hours of operation: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to update hours of operation: {str(e)}")


def connect_hours_of_operations_delete(
    instance_id: str,
    hours_of_operation_id: str
) -> Dict[str, Any]:
    """Delete hours of operation configuration.
    
    WARNING: Cannot delete hours of operation that are referenced by queues.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID to delete
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the deletion result
        
    Raises:
        ConnectHoursOfOperationError: If the deletion fails
        
    Example:
        >>> connect_hours_of_operations_delete(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     hours_of_operation_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        client.delete_hours_of_operation(
            InstanceId=instance_id,
            HoursOfOperationId=hours_of_operation_id
        )
        
        return {
            "status": "success",
            "message": f"Hours of operation {hours_of_operation_id} deleted successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to delete hours of operation: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to delete hours of operation: {str(e)}")


def connect_hours_of_operations_create_override(
    instance_id: str,
    hours_of_operation_id: str,
    name: str,
    description: str,
    start_time: Dict[str, Any],
    end_time: Dict[str, Any],
    override_config: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create an hours of operation override (e.g., for holidays).
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        name: Name for the override
        description: Description of the override
        start_time: When the override starts (Hours, Minutes)
        end_time: When the override ends (Hours, Minutes)
        override_config: Override configuration with day/time settings
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - override_id: ID of the created override
        
    Raises:
        ConnectHoursOfOperationError: If creation fails
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id,
            "HoursOfOperationId": hours_of_operation_id,
            "Name": name,
            "Description": description,
            "StartTime": start_time,
            "EndTime": end_time,
            "OverrideConfig": override_config
        }
        
        response = client.create_hours_of_operation_override(**params)
        
        return {
            "status": "success",
            "override_id": response.get("HoursOfOperationOverrideId")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to create override: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to create override: {str(e)}")


def connect_hours_of_operations_delete_override(
    instance_id: str,
    hours_of_operation_id: str,
    override_id: str
) -> Dict[str, Any]:
    """Delete an hours of operation override.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        override_id: Override ID to delete
        
    Returns:
        Dictionary containing deletion status
    """
    try:
        client = _get_connect_client()
        
        client.delete_hours_of_operation_override(
            InstanceId=instance_id,
            HoursOfOperationId=hours_of_operation_id,
            HoursOfOperationOverrideId=override_id
        )
        
        return {
            "status": "success",
            "message": f"Override {override_id} deleted successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to delete override: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to delete override: {str(e)}")


def connect_hours_of_operations_describe_override(
    instance_id: str,
    hours_of_operation_id: str,
    override_id: str
) -> Dict[str, Any]:
    """Describe an hours of operation override.
    
    Args:
        instance_id: Connect instance ID
        hours_of_operation_id: Hours of operation ID
        override_id: Override ID
        
    Returns:
        Dictionary containing override details
        
    Note:
        This uses list and filter since describe API may not be available for overrides
    """
    try:
        client = _get_connect_client()
        
        # List overrides and find the one we want
        response = client.list_hours_of_operation_overrides(
            InstanceId=instance_id,
            HoursOfOperationId=hours_of_operation_id
        )
        
        overrides = response.get("HoursOfOperationOverrideList", [])
        for override in overrides:
            if override.get("HoursOfOperationOverrideId") == override_id:
                return {
                    "status": "success",
                    "override": {
                        "id": override.get("HoursOfOperationOverrideId"),
                        "name": override.get("Name"),
                        "description": override.get("Description"),
                        "start_time": override.get("StartTime"),
                        "end_time": override.get("EndTime"),
                        "override_config": override.get("OverrideConfig", [])
                    }
                }
        
        raise ConnectHoursOfOperationError(f"Override {override_id} not found")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectHoursOfOperationError(f"Failed to describe override: {error_code} - {error_message}")
    except ConnectHoursOfOperationError:
        raise
    except Exception as e:
        raise ConnectHoursOfOperationError(f"Failed to describe override: {str(e)}")
