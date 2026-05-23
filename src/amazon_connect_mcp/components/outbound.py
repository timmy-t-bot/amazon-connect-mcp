"""Amazon Connect MCP Server - Outbound Communication Tools.

This module provides MCP tools for initiating outbound voice contacts
in Amazon Connect, including:
- Starting outbound voice contacts with dynamic attributes
- Passing custom attributes to contact flows
- Supporting both direct phone number and queue-based calling
"""

import json
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    OUTBOUND_AVAILABLE = True
except Exception:
    connect_client = None
    OUTBOUND_AVAILABLE = False


class ConnectOutboundError(Exception):
    """Exception raised for Connect outbound call operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_start_outbound_voice_contact(
    instance_id: str,
    destination_phone_number: str,
    contact_flow_id: str,
    source_phone_number: str = "",
    queue_id: str = "",
    attributes: Optional[Dict[str, str]] = None,
    client_token: str = "",
    answer_machine_detection_config: Optional[Dict[str, Any]] = None,
    campaign_id: str = "",
    traffic_type: str = "GENERAL",
) -> Dict[str, Any]:
    """Start an outbound voice contact (place a call) via Amazon Connect.

    This is the primary tool for making outbound calls. The contact flow
    specified by `contact_flow_id` will be executed when the call connects.
    Use `attributes` to pass dynamic data (like messages, customer info) that
    the contact flow can read via `$.Attributes.<key>`.

    Args:
        instance_id: Connect instance ID (required)
        destination_phone_number: The phone number to call in E.164 format
            (e.g., +1-415-555-0100). Required.
        contact_flow_id: The ID of the contact flow to execute when the call
            connects. Required.
        source_phone_number: The source (caller ID) phone number. Must be a
            phone number already claimed in your Connect instance. Required
            for outbound calls unless the queue has an outbound caller config.
        queue_id: The queue to associate the contact with. Required for
            placing the call in a queue.
        attributes: Dictionary of custom attributes to pass to the contact
            flow. These can be referenced in the flow as
            `$.Attributes.<key>`. For example:
            {"message": "Your appointment is confirmed", "customer_name": "John"}
            A Play prompt node can read this via `$.Attributes.message`.
        client_token: Unique idempotency token to prevent duplicate calls
            (max 500 chars). Auto-generated if not provided.
        answer_machine_detection_config: Optional configuration for detecting
            answering machines. Dict with:
            - EnableAnswerMachineDetection: bool
            - AwaitAnswerMachinePrompt: bool (optional)
        campaign_id: Optional campaign ID for outbound campaign tracking.
        traffic_type: Type of traffic. 'GENERAL' (default) or 'CAMPAIGN'.

    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - contact_id: The ID of the created contact (call)
        - contact_arn: The ARN of the contact
        - destination_phone_number: The number that was called
        - attributes: The attributes that were passed (if any)

    Raises:
        ConnectOutboundError: If the call cannot be initiated

    Example:
        >>> # Simple outbound call with a message
        >>> connect_start_outbound_voice_contact(
        ...     instance_id="12345678-1234-...",
        ...     destination_phone_number="+1-415-555-0100",
        ...     contact_flow_id="abcdef12-1234-...",
        ...     source_phone_number="+1-800-555-0123",
        ...     queue_id="queue-12345678-...",
        ...     attributes={
        ...         "message": "Your appointment is confirmed for tomorrow at 2PM",
        ...         "customer_name": "Jane Smith"
        ...     }
        ... )

        >>> # Call with answer machine detection
        >>> connect_start_outbound_voice_contact(
        ...     instance_id="12345678-1234-...",
        ...     destination_phone_number="+1-415-555-0100",
        ...     contact_flow_id="abcdef12-1234-...",
        ...     source_phone_number="+1-800-555-0123",
        ...     queue_id="queue-12345678-...",
        ...     answer_machine_detection_config={
        ...         "EnableAnswerMachineDetection": True,
        ...         "AwaitAnswerMachinePrompt": True
        ...     }
        ... )
    """
    try:
        client = _get_connect_client()

        # Build parameters
        params: Dict[str, Any] = {
            "InstanceId": instance_id,
            "DestinationPhoneNumber": destination_phone_number,
            "ContactFlowId": contact_flow_id,
        }

        # Source phone number (caller ID)
        if source_phone_number:
            params["SourcePhoneNumber"] = source_phone_number

        # Queue ID
        if queue_id:
            params["QueueId"] = queue_id

        # Custom attributes
        if attributes:
            params["Attributes"] = attributes

        # Idempotency token
        if client_token:
            params["ClientToken"] = client_token

        # Answer machine detection
        if answer_machine_detection_config:
            params["AnswerMachineDetectionConfig"] = answer_machine_detection_config

        # Campaign info
        if campaign_id:
            params["CampaignId"] = campaign_id

        # Traffic type
        if traffic_type:
            params["TrafficType"] = traffic_type

        response = client.start_outbound_voice_contact(**params)

        return {
            "status": "success",
            "contact_id": response.get("ContactId"),
            "contact_arn": response.get("ContactArn"),
            "destination_phone_number": destination_phone_number,
            "source_phone_number": source_phone_number or "queue-default",
            "attributes": attributes if attributes else {},
            "message": f"Outbound call initiated to {destination_phone_number}"
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectOutboundError(
            f"Failed to start outbound voice contact: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectOutboundError(
            f"Failed to start outbound voice contact: {str(e)}"
        )


def connect_stop_contact(
    instance_id: str,
    contact_id: str,
) -> Dict[str, Any]:
    """Stop an active contact (end a call).

    Args:
        instance_id: Connect instance ID
        contact_id: The ID of the contact to stop

    Returns:
        Dictionary with stop status

    Raises:
        ConnectOutboundError: If the stop operation fails

    Example:
        >>> connect_stop_contact(
        ...     instance_id="12345678-1234-...",
        ...     contact_id="abcdef-1234-..."
        ... )
    """
    try:
        client = _get_connect_client()

        response = client.stop_contact(
            InstanceId=instance_id,
            ContactId=contact_id,
        )

        return {
            "status": "success",
            "contact_id": contact_id,
            "message": f"Contact {contact_id} stopped successfully"
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectOutboundError(
            f"Failed to stop contact: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectOutboundError(f"Failed to stop contact: {str(e)}")


def connect_describe_contact(
    instance_id: str,
    contact_id: str,
) -> Dict[str, Any]:
    """Describe an active or recently completed contact.

    Args:
        instance_id: Connect instance ID
        contact_id: The ID of the contact to describe

    Returns:
        Dictionary with contact details including:
        - contact_id, arn, channel, initiation_method
        - queue_info, agent_info (if assigned)
        - attributes that were passed to the contact
        - disconnect_reason (if disconnected)

    Example:
        >>> contact = connect_describe_contact(
        ...     instance_id="12345678-1234-...",
        ...     contact_id="abcdef-1234-..."
        ... )
    """
    try:
        client = _get_connect_client()

        response = client.describe_contact(
            InstanceId=instance_id,
            ContactId=contact_id,
        )

        contact = response.get("Contact", {})

        return {
            "status": "success",
            "contact_id": contact.get("Id"),
            "arn": contact.get("Arn"),
            "channel": contact.get("Channel"),
            "initiation_method": contact.get("InitiationMethod"),
            "initiation_timestamp": contact.get("InitiationTimestamp"),
            "disconnect_timestamp": contact.get("DisconnectTimestamp"),
            "last_update_timestamp": contact.get("LastUpdateTimestamp"),
            "queue_info": contact.get("QueueInfo"),
            "agent_info": contact.get("AgentInfo"),
            "attributes": contact.get("Attributes", {}),
            "disconnect_reason": contact.get("DisconnectReason"),
            "initial_contact_id": contact.get("InitialContactId"),
            "previous_contact_id": contact.get("PreviousContactId"),
            "tags": contact.get("Tags", {}),
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectOutboundError(
            f"Failed to describe contact: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectOutboundError(f"Failed to describe contact: {str(e)}")


def connect_update_contact_attributes(
    instance_id: str,
    contact_id: str,
    attributes: Dict[str, str],
) -> Dict[str, Any]:
    """Update attributes on an active contact.

    This allows mid-call updates to contact flow variables, enabling
    dynamic behavior changes during a call.

    Args:
        instance_id: Connect instance ID
        contact_id: The ID of the active contact
        attributes: Dictionary of attribute key-value pairs to set.
            These will be available in the contact flow as
            `$.Attributes.<key>`.

    Returns:
        Dictionary with update status

    Example:
        >>> connect_update_contact_attributes(
        ...     instance_id="12345678-1234-...",
        ...     contact_id="abcdef-1234-...",
        ...     attributes={"verified": "true", "priority": "high"}
        ... )
    """
    try:
        client = _get_connect_client()

        client.update_contact_attributes(
            InstanceId=instance_id,
            InitialContactId=contact_id,
            Attributes=attributes,
        )

        return {
            "status": "success",
            "contact_id": contact_id,
            "attributes_set": list(attributes.keys()),
            "message": f"Updated {len(attributes)} attributes on contact {contact_id}"
        }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectOutboundError(
            f"Failed to update contact attributes: {error_code} - {error_message}"
        )
    except Exception as e:
        raise ConnectOutboundError(
            f"Failed to update contact attributes: {str(e)}"
        )
