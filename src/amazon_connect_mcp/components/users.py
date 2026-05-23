"""Amazon Connect MCP Server - User/Agent Management Tools.

This module provides MCP tools for managing users and agents in Amazon Connect:
- Listing users for an instance
- Describing user details
- Creating users
- Updating user configurations
"""

from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    USERS_AVAILABLE = True
except Exception:
    connect_client = None
    USERS_AVAILABLE = False


class ConnectUserError(Exception):
    """Exception raised for user operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_users_list(
    instance_id: str,
    max_results: int = 50,
    next_token: str = "",
) -> Dict[str, Any]:
    """List all users/agents for a Connect instance.

    This is essential for managing agents who will handle outbound calls,
    assigning routing profiles, and monitoring agent availability.

    Args:
        instance_id: Connect instance ID (required)
        max_results: Maximum number of results (default 50, max 1000)
        next_token: Token for pagination

    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - users: List of user summaries
          Each with: id, arn, username, phone_config, security_profile_ids,
          routing_profile_id, identity_info, tags
        - next_token: Pagination token

    Raises:
        ConnectUserError: If the list operation fails

    Example:
        >>> users = connect_users_list(
        ...     instance_id="12345678-1234-..."
        ... )
        >>> for u in users["users"]:
        ...     print(f"{u['username']}: {u['routing_profile_id']}")
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

        response = client.list_users(**params)

        users = []
        for user in response.get("UserSummaryList", []):
            users.append({
                "id": user.get("Id"),
                "arn": user.get("Arn"),
                "username": user.get("Username"),
                "display_name": user.get("IdentityInfo", {}).get("FirstName", "") +
                    " " + user.get("IdentityInfo", {}).get("LastName", ""),
                "phone_type": user.get("PhoneConfig", {}).get("PhoneType"),
                "phone_number": user.get("PhoneConfig", {}).get("DeskPhoneNumber"),
                "security_profile_ids": user.get("SecurityProfileIds", []),
                "routing_profile_id": user.get("RoutingProfileId"),
                "hierarchy_group_id": user.get("HierarchyGroupId"),
                "tags": user.get("Tags", {}),
            })

        return {
            "status": "success",
            "users": users,
            "next_token": response.get("NextToken"),
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectUserError(
            f"Failed to list users: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectUserError(f"Failed to list users: {str(e)}")


def connect_users_describe(
    instance_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """Get detailed information about a user/agent.

    Args:
        instance_id: Connect instance ID
        user_id: User ID

    Returns:
        Dictionary with user details:
        - id, arn, username
        - identity_info: FirstName, LastName, Email
        - phone_config: PhoneType, DeskPhoneNumber, AfterContactWorkTimeLimit,
          AutoAccept
        - security_profile_ids: List of assigned security profiles
        - routing_profile_id: Assigned routing profile
        - hierarchy_group_id: Org hierarchy placement
        - directory_user_id: Directory service ID
        - tags

    Raises:
        ConnectUserError: If the describe operation fails

    Example:
        >>> user = connect_users_describe(
        ...     instance_id="12345678-1234-...",
        ...     user_id="user-12345678-..."
        ... )
    """
    try:
        client = _get_connect_client()

        response = client.describe_user(
            InstanceId=instance_id,
            UserId=user_id,
        )

        user = response.get("User", {})

        return {
            "status": "success",
            "id": user.get("Id"),
            "arn": user.get("Arn"),
            "username": user.get("Username"),
            "identity_info": {
                "first_name": user.get("IdentityInfo", {}).get("FirstName"),
                "last_name": user.get("IdentityInfo", {}).get("LastName"),
                "email": user.get("IdentityInfo", {}).get("Email"),
            },
            "phone_config": {
                "phone_type": user.get("PhoneConfig", {}).get("PhoneType"),
                "desk_phone_number": user.get("PhoneConfig", {}).get("DeskPhoneNumber"),
                "after_contact_work_time_limit":
                    user.get("PhoneConfig", {}).get("AfterContactWorkTimeLimit"),
                "auto_accept": user.get("PhoneConfig", {}).get("AutoAccept"),
            },
            "security_profile_ids": user.get("SecurityProfileIds", []),
            "routing_profile_id": user.get("RoutingProfileId"),
            "hierarchy_group_id": user.get("HierarchyGroupId"),
            "directory_user_id": user.get("DirectoryUserId"),
            "tags": user.get("Tags", {}),
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectUserError(
            f"Failed to describe user: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectUserError(f"Failed to describe user: {str(e)}")
