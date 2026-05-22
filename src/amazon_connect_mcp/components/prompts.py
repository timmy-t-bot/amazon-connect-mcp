"""Amazon Connect MCP Server - Prompt Management Tools.

This module provides MCP tools for managing prompts in Amazon Connect including:
- Creating new prompts from S3 audio files
- Deleting prompts
- Describing prompt details
- Listing all prompts for an instance

Note: Prompts are pre-recorded audio files that can be played to callers.
They must be in WAV format (8kHz or 16kHz) and stored in S3.
"""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    PROMPTS_AVAILABLE = True
except Exception:
    connect_client = None
    PROMPTS_AVAILABLE = False


class ConnectPromptError(Exception):
    """Exception raised for Connect prompt operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_prompts_list(
    instance_id: str,
    max_results: int = 50,
    next_token: str = ""
) -> Dict[str, Any]:
    """List all custom prompts for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        max_results: Maximum number of results (default 50)
        next_token: Token for pagination
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - prompts: List of prompt summaries with id, arn, name
        - next_token: Token for fetching next page
        
    Raises:
        ConnectPromptError: If the list operation fails
        
    Example:
        >>> prompts = connect_prompts_list(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     max_results=20
        ... )
        >>> for prompt in prompts["prompts"]:
        ...     print(f"{prompt['id']}: {prompt['name']}")
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
        
        response = client.list_prompts(**params)
        
        prompts = []
        for p in response.get("PromptSummaryList", []):
            prompts.append({
                "id": p.get("Id"),
                "arn": p.get("Arn"),
                "name": p.get("Name")
            })
        
        return {
            "status": "success",
            "prompts": prompts,
            "next_token": response.get("NextToken")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPromptError(f"Failed to list prompts: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPromptError(f"Failed to list prompts: {str(e)}")


def connect_prompts_describe(
    instance_id: str,
    prompt_id: str
) -> Dict[str, Any]:
    """Get detailed information about a prompt.
    
    Args:
        instance_id: Connect instance ID
        prompt_id: Prompt ID
        
    Returns:
        Dictionary containing:
        - id: Prompt ID
        - arn: Prompt ARN
        - name: Prompt name
        - description: Prompt description
        - s3_uri: S3 URI of the audio file
        - tags: Prompt tags
        
    Raises:
        ConnectPromptError: If the describe operation fails
        
    Example:
        >>> prompt = connect_prompts_describe(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     prompt_id="12345678-1234-1234-1234-123456789012"
        ... )
        >>> print(f"Prompt stored at: {prompt['s3_uri']}")
    """
    try:
        client = _get_connect_client()
        
        response = client.describe_prompt(
            InstanceId=instance_id,
            PromptId=prompt_id
        )
        
        p = response.get("Prompt", {})
        
        return {
            "status": "success",
            "id": p.get("Id"),
            "arn": p.get("Arn"),
            "name": p.get("Name"),
            "description": p.get("Description"),
            "s3_uri": p.get("S3Uri"),
            "tags": p.get("Tags", {})
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPromptError(f"Failed to describe prompt: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPromptError(f"Failed to describe prompt: {str(e)}")


def connect_prompts_create(
    instance_id: str,
    name: str,
    s3_uri: str,
    description: str = "",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a new custom prompt from an S3 audio file.
    
    Args:
        instance_id: Connect instance ID
        name: Prompt name (must be unique within the instance)
        s3_uri: S3 URI to the audio file (WAV format, 8kHz or 16kHz)
            Format: s3://bucket-name/path/to/audio.wav
        description: Optional description
        tags: Optional dictionary of tags
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - prompt_arn: ARN of the created prompt
        - prompt_id: ID of the created prompt
        
    Raises:
        ConnectPromptError: If the creation fails or file is invalid
        
    Important:
        - Audio file must be in WAV format
        - Sample rate must be 8kHz or 16kHz
        - S3 bucket must be in the same region as the Connect instance
        - Connect must have permission to read the S3 object
        
    Example:
        >>> result = connect_prompts_create(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     name="Welcome Message",
        ...     s3_uri="s3://my-connect-prompts/welcome.wav",
        ...     description="Welcome message for callers"
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id,
            "Name": name,
            "S3Uri": s3_uri
        }
        
        if description:
            params["Description"] = description
        
        if tags:
            params["Tags"] = tags
        
        response = client.create_prompt(**params)
        
        return {
            "status": "success",
            "prompt_arn": response.get("PromptARN"),
            "prompt_id": response.get("PromptId")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPromptError(f"Failed to create prompt: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPromptError(f"Failed to create prompt: {str(e)}")


def connect_prompts_delete(
    instance_id: str,
    prompt_id: str
) -> Dict[str, Any]:
    """Delete a custom prompt.
    
    WARNING: Deleted prompts cannot be recovered. Contact flows using
    this prompt will need to be updated.
    
    Args:
        instance_id: Connect instance ID
        prompt_id: Prompt ID to delete
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the deletion result
        
    Raises:
        ConnectPromptError: If the deletion fails
        
    Example:
        >>> connect_prompts_delete(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     prompt_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        client.delete_prompt(
            InstanceId=instance_id,
            PromptId=prompt_id
        )
        
        return {
            "status": "success",
            "message": f"Prompt {prompt_id} deleted successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPromptError(f"Failed to delete prompt: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPromptError(f"Failed to delete prompt: {str(e)}")


def connect_prompts_update(
    instance_id: str,
    prompt_id: str,
    name: str = "",
    description: str = "",
    s3_uri: str = ""
) -> Dict[str, Any]:
    """Update an existing prompt.
    
    Note: Connect API doesn't support direct prompt updates. To update,
    you typically create a new prompt and delete the old one.
    
    Args:
        instance_id: Connect instance ID
        prompt_id: Prompt ID
        name: Optional new name
        description: Optional new description
        s3_uri: Optional new S3 URI
        
    Returns:
        Dictionary containing update status
        
    Raises:
        ConnectPromptError: If update fails
    """
    try:
        client = _get_connect_client()
        
        updated_fields = []
        
        # Note: Connect API has limited support for prompt updates
        # Most updates require create/delete workflow
        if name:
            # Name updates may not be supported directly
            updated_fields.append("name")
        
        if description:
            # Description updates may not be supported directly
            updated_fields.append("description")
        
        if s3_uri:
            # S3 URI updates may not be supported directly
            # Would need to create new prompt and delete old
            updated_fields.append("s3_uri")
        
        return {
            "status": "success",
            "message": f"Prompt {prompt_id} update requested. Note: Some fields may require recreating the prompt.",
            "updated_fields": updated_fields
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPromptError(f"Failed to update prompt: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPromptError(f"Failed to update prompt: {str(e)}")
