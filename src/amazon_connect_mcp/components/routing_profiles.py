"""Amazon Connect MCP Server - Routing Profile Management Tools.

This module provides MCP tools for managing routing profiles in Amazon Connect:
- Listing routing profiles for an instance
- Describing routing profile details
- Creating routing profiles
- Updating routing profiles
"""

from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    ROUTING_AVAILABLE = True
except Exception:
    connect_client = None
    ROUTING_AVAILABLE = False


class ConnectRoutingProfileError(Exception):
    """Exception raised for routing profile operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_routing_profiles_list(
    instance_id: str,
    max_results: int = 50,
    next_token: str = "",
) -> Dict[str, Any]:
    """List all routing profiles for a Connect instance.

    Routing profiles define the channels and queues that agents can use.
    This is essential for setting up outbound calling capabilities and
    assigning agents to outbound queues.

    Args:
        instance_id: Connect instance ID (required)
        max_results: Maximum number of results (default 50)
        next_token: Token for pagination

    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - routing_profiles: List of routing profile summaries
          Each with: id, arn, name, description, number_of_associated_queues,
          number_of_associated_users, channel_concurrency, tags
        - next_token: Pagination token

    Raises:
        ConnectRoutingProfileError: If the list operation fails

    Example:
        >>> profiles = connect_routing_profiles_list(
        ...     instance_id="12345678-1234-..."
        ... )
        >>> for rp in profiles["routing_profiles"]:
        ...     print(f"{rp['name']}: {rp['number_of_associated_queues']} queues")
    """
    try:
        client = _get_connect_client()

        params: Dict[str, Any] = {
            "InstanceId": instance_id,
        }

        if max_results:
            params["MaxResults"] = min(max_results, 1000)

        if next_token:
            params["NextToken"] = next_token

        response = client.list_routing_profiles(**params)

        routing_profiles = []
        for rp in response.get("RoutingProfileSummaryList", []):
            routing_profiles.append({
                "id": rp.get("Id"),
                "arn": rp.get("Arn"),
                "name": rp.get("Name"),
                "description": rp.get("Description", ""),
                "number_of_associated_queues": rp.get("NumberOfAssociatedQueues", 0),
                "number_of_associated_users": rp.get("NumberOfAssociatedUsers", 0),
                "channel_concurrency": rp.get("ChannelConcurrency", {}),
                "default_outbound_queue_id": rp.get("DefaultOutboundQueueId"),
                "tags": rp.get("Tags", {}),
            })

        return {
            "status": "success",
            "routing_profiles": routing_profiles,
            "next_token": response.get("NextToken"),
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectRoutingProfileError(
            f"Failed to list routing profiles: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectRoutingProfileError(
            f"Failed to list routing profiles: {str(e)}"
        )


def connect_routing_profiles_describe(
    instance_id: str,
    routing_profile_id: str,
) -> Dict[str, Any]:
    """Get detailed information about a routing profile.

    Args:
        instance_id: Connect instance ID
        routing_profile_id: Routing profile ID

    Returns:
        Dictionary with routing profile details:
        - id, arn, name, description
        - media_concurrencies: Channel concurrency settings
        - default_outbound_queue_id: Default queue for outbound calls
        - queues: List of associated queue configs (id, arn, name, priority, delay)
        - number_of_associated_queues, number_of_associated_users
        - tags

    Raises:
        ConnectRoutingProfileError: If the describe operation fails

    Example:
        >>> profile = connect_routing_profiles_describe(
        ...     instance_id="12345678-1234-...",
        ...     routing_profile_id="rp-12345678-..."
        ... )
    """
    try:
        client = _get_connect_client()

        response = client.describe_routing_profile(
            InstanceId=instance_id,
            RoutingProfileId=routing_profile_id,
        )

        rp = response.get("RoutingProfile", {})

        # Format queue configs
        queues = []
        for qc in rp.get("QueueConfigs", []):
            queues.append({
                "queue_id": qc.get("QueueReference", {}).get("QueueId"),
                "queue_arn": qc.get("QueueReference", {}).get("Channel"),
                "priority": qc.get("Priority"),
                "delay": qc.get("Delay"),
            })

        return {
            "status": "success",
            "id": rp.get("RoutingProfileId"),
            "arn": rp.get("RoutingProfileArn"),
            "name": rp.get("Name"),
            "description": rp.get("Description", ""),
            "media_concurrencies": rp.get("MediaConcurrencies", []),
            "default_outbound_queue_id": rp.get("DefaultOutboundQueueId"),
            "queues": queues,
            "number_of_associated_queues": rp.get("NumberOfAssociatedQueues", 0),
            "number_of_associated_users": rp.get("NumberOfAssociatedUsers", 0),
            "tags": rp.get("Tags", {}),
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectRoutingProfileError(
            f"Failed to describe routing profile: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectRoutingProfileError(
            f"Failed to describe routing profile: {str(e)}"
        )
