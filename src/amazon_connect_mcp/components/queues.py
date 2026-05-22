"""Amazon Connect MCP Server - Queue Management Tools.

This module provides MCP tools for managing queues in Amazon Connect including:
- Creating new queues
- Updating existing queues
- Deleting queues
- Describing queue details
- Listing all queues for an instance
"""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    QUEUES_AVAILABLE = True
except Exception:
    connect_client = None
    QUEUES_AVAILABLE = False


class ConnectQueueError(Exception):
    """Exception raised for Connect queue operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_queues_list(
    instance_id: str,
    queue_types: Optional[List[str]] = None,
    max_results: int = 50,
    next_token: str = ""
) -> Dict[str, Any]:
    """List all queues for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        queue_types: Optional list of queue types to filter ('STANDARD', 'AGENT')
        max_results: Maximum number of results (default 50)
        next_token: Token for pagination
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - queues: List of queue summaries with id, arn, name, type, etc.
        - next_token: Token for fetching next page
        
    Raises:
        ConnectQueueError: If the list operation fails
        
    Example:
        >>> queues = connect_queues_list(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     queue_types=["STANDARD"]
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id
        }
        
        if queue_types:
            params["QueueTypes"] = queue_types
        
        if max_results:
            params["MaxResults"] = max_results
        
        if next_token:
            params["NextToken"] = next_token
        
        response = client.list_queues(**params)
        
        queues = []
        for q in response.get("QueueSummaryList", []):
            queues.append({
                "id": q.get("Id"),
                "arn": q.get("Arn"),
                "name": q.get("Name"),
                "queue_type": q.get("QueueType"),
                "description": q.get("Description"),
                "status": q.get("Status"),
                "tags": q.get("Tags", {})
            })
        
        return {
            "status": "success",
            "queues": queues,
            "next_token": response.get("NextToken")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectQueueError(f"Failed to list queues: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectQueueError(f"Failed to list queues: {str(e)}")


def connect_queues_describe(
    instance_id: str,
    queue_id: str
) -> Dict[str, Any]:
    """Get detailed information about a queue.
    
    Args:
        instance_id: Connect instance ID
        queue_id: Queue ID
        
    Returns:
        Dictionary containing:
        - id: Queue ID
        - arn: Queue ARN
        - name: Queue name
        - description: Queue description
        - type: Queue type (STANDARD, AGENT)
        - status: Queue status
        - hours_of_operation_id: Associated hours of operation ID
        - max_contacts: Maximum number of contacts allowed
        - outbound_caller_config: Outbound calling configuration
        - quick_connect_ids: List of associated quick connect IDs
        - tags: Queue tags
        
    Raises:
        ConnectQueueError: If the queue doesn't exist or API call fails
        
    Example:
        >>> queue = connect_queues_describe(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     queue_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        response = client.describe_queue(
            InstanceId=instance_id,
            QueueId=queue_id
        )
        
        q = response.get("Queue", {})
        
        return {
            "status": "success",
            "id": q.get("Id"),
            "arn": q.get("Arn"),
            "name": q.get("Name"),
            "description": q.get("Description"),
            "queue_type": q.get("QueueType"),
            "status": q.get("Status"),
            "hours_of_operation_id": q.get("HoursOfOperationId"),
            "max_contacts": q.get("MaxContacts"),
            "outbound_caller_config": q.get("OutboundCallerConfig"),
            "quick_connect_ids": q.get("QuickConnectIds", []),
            "tags": q.get("Tags", {})
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectQueueError(f"Failed to describe queue: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectQueueError(f"Failed to describe queue: {str(e)}")


def connect_queues_create(
    instance_id: str,
    name: str,
    hours_of_operation_id: str,
    description: str = "",
    max_contacts: Optional[int] = None,
    quick_connect_ids: Optional[List[str]] = None,
    tags: Optional[Dict[str, str]] = None,
    outbound_caller_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new queue.
    
    Args:
        instance_id: Connect instance ID
        name: Queue name (required)
        hours_of_operation_id: Hours of operation ID (required)
        description: Optional description
        max_contacts: Optional maximum number of contacts allowed in queue
        quick_connect_ids: Optional list of quick connect IDs
        tags: Optional dictionary of tags
        outbound_caller_config: Optional outbound caller configuration with:
            - OutboundCallerIdName: Name displayed to callers
            - OutboundCallerIdNumberId: ID of phone number for caller ID
            - OutboundFlowId: Contact flow ID for outbound calls
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - queue_id: ID of the created queue
        - queue_arn: ARN of the created queue
        
    Raises:
        ConnectQueueError: If the creation fails
        
    Example:
        >>> result = connect_queues_create(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     name="Support Queue",
        ...     hours_of_operation_id="12345678-1234-1234-1234-123456789012",
        ...     description="Default support queue",
        ...     max_contacts=100
        ... )
    """
    try:
        client = _get_connect_client()
        
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
        
        if tags:
            params["Tags"] = tags
        
        if outbound_caller_config:
            params["OutboundCallerConfig"] = outbound_caller_config
        
        response = client.create_queue(**params)
        
        return {
            "status": "success",
            "queue_id": response.get("QueueId"),
            "queue_arn": response.get("QueueArn")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectQueueError(f"Failed to create queue: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectQueueError(f"Failed to create queue: {str(e)}")


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
        status: Optional new status ('ENABLED' or 'DISABLED')
        quick_connect_ids: Optional new list of quick connect IDs
        outbound_caller_config: Optional outbound caller configuration
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the update
        - updated_fields: List of fields that were updated
        
    Raises:
        ConnectQueueError: If the update fails
        
    Example:
        >>> connect_queues_update(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     queue_id="12345678-1234-1234-1234-123456789012",
        ...     max_contacts=50,
        ...     status="ENABLED"
        ... )
    """
    try:
        client = _get_connect_client()
        
        updated_fields = []
        
        # Update queue configuration
        if hours_of_operation_id or max_contacts is not None or outbound_caller_config:
            update_params = {
                "InstanceId": instance_id,
                "QueueId": queue_id
            }
            
            if hours_of_operation_id:
                update_params["HoursOfOperationId"] = hours_of_operation_id
                updated_fields.append("hours_of_operation_id")
            
            if max_contacts is not None:
                update_params["MaxContacts"] = max_contacts
                updated_fields.append("max_contacts")
            
            if outbound_caller_config:
                update_params["OutboundCallerConfig"] = outbound_caller_config
                updated_fields.append("outbound_caller_config")
            
            if quick_connect_ids is not None:
                update_params["QuickConnectIds"] = quick_connect_ids
                updated_fields.append("quick_connect_ids")
            
            # Only call update if we have parameters beyond InstanceId and QueueId
            if len(update_params) > 2:
                client.update_queue(**update_params)
        
        # Update name separately
        if name:
            client.update_queue_name(
                InstanceId=instance_id,
                QueueId=queue_id,
                Name=name
            )
            updated_fields.append("name")
        
        # Update description separately
        if description:
            client.update_queue_name(
                InstanceId=instance_id,
                QueueId=queue_id,
                Description=description
            )
            updated_fields.append("description")
        
        # Update status separately
        if status:
            client.update_queue_status(
                InstanceId=instance_id,
                QueueId=queue_id,
                Status=status
            )
            updated_fields.append("status")
        
        return {
            "status": "success",
            "message": f"Queue {queue_id} updated successfully",
            "updated_fields": updated_fields
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectQueueError(f"Failed to update queue: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectQueueError(f"Failed to update queue: {str(e)}")


def connect_queues_delete(
    instance_id: str,
    queue_id: str
) -> Dict[str, Any]:
    """Delete a queue.
    
    WARNING: Deleting a queue that is referenced by contact flows or
    other resources may cause errors.
    
    Args:
        instance_id: Connect instance ID
        queue_id: Queue ID to delete
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the deletion result
        
    Raises:
        ConnectQueueError: If the deletion fails
        
    Example:
        >>> connect_queues_delete(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     queue_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        client.delete_queue(
            InstanceId=instance_id,
            QueueId=queue_id
        )
        
        return {
            "status": "success",
            "message": f"Queue {queue_id} deleted successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectQueueError(f"Failed to delete queue: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectQueueError(f"Failed to delete queue: {str(e)}")
