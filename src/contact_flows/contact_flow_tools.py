"""Amazon Connect MCP Server - Contact Flow Tools."""

import json
import boto3
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from ..templates.engine import TemplateEngine
from ..templates.registry import TemplateRegistry

# Initialize MCP server
mcp = FastMCP("amazon_connect_contact_flows")

# Initialize AWS clients
connect_client = boto3.client("connect")

# Initialize template components
template_engine = TemplateEngine()
template_registry = TemplateRegistry()


@mcp.tool()
def contact_flows_list(
    instance_id: str,
    contact_flow_types: Optional[List[str]] = None,
    max_results: int = 100
) -> Dict[str, Any]:
    """List contact flows in an Amazon Connect instance.
    
    Args:
        instance_id: The ID of the Connect instance
        contact_flow_types: Optional filter by flow types (e.g., CONTACT_FLOW, OUTBOUND_WHISPER_FLOW)
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary containing list of contact flows
    """
    try:
        params = {
            "InstanceId": instance_id,
            "MaxResults": max_results
        }
        
        if contact_flow_types:
            params["ContactFlowTypes"] = contact_flow_types
        
        response = connect_client.list_contact_flows(**params)
        
        return {
            "status": "success",
            "contact_flows": [
                {
                    "id": flow["Id"],
                    "arn": flow["Arn"],
                    "name": flow["Name"],
                    "type": flow["Type"],
                    "description": flow.get("Description", ""),
                    "state": flow.get("State", "ACTIVE"),
                    "last_modified_time": flow.get("LastModifiedTime"),
                    "last_modified_region": flow.get("LastModifiedRegion")
                }
                for flow in response.get("ContactFlowSummaryList", [])
            ],
            "next_token": response.get("NextToken")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_describe(
    instance_id: str,
    contact_flow_id: str
) -> Dict[str, Any]:
    """Describe a contact flow and retrieve its content.
    
    Args:
        instance_id: The ID of the Connect instance
        contact_flow_id: The ID of the contact flow to describe
        
    Returns:
        Dictionary containing contact flow details and content
    """
    try:
        response = connect_client.describe_contact_flow(
            InstanceId=instance_id,
            ContactFlowId=contact_flow_id
        )
        
        contact_flow = response["ContactFlow"]
        
        # Try to parse content as JSON
        content_str = contact_flow.get("Content", "{}")
        try:
            content_json = json.loads(content_str)
        except json.JSONDecodeError:
            content_json = {"raw_content": content_str}
        
        return {
            "status": "success",
            "contact_flow": {
                "id": contact_flow["Id"],
                "arn": contact_flow["Arn"],
                "name": contact_flow["Name"],
                "type": contact_flow["Type"],
                "description": contact_flow.get("Description", ""),
                "state": contact_flow["State"],
                "created_time": contact_flow.get("CreatedTime"),
                "last_modified_time": contact_flow.get("LastModifiedTime"),
                "last_modified_region": contact_flow.get("LastModifiedRegion"),
                "content": content_json,
                "tags": contact_flow.get("Tags", {})
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_create(
    instance_id: str,
    name: str,
    content: str,
    type: str = "CONTACT_FLOW",
    description: str = "",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a new contact flow with raw JSON content.
    
    Args:
        instance_id: The ID of the Connect instance
        name: Name for the contact flow
        content: JSON string containing the flow definition
        type: Type of contact flow (CONTACT_FLOW, OUTBOUND_WHISPER_FLOW, etc.)
        description: Optional description for the flow
        tags: Optional tags for the contact flow
        
    Returns:
        Dictionary containing the created contact flow ID and ARN
    """
    try:
        params = {
            "InstanceId": instance_id,
            "Name": name,
            "Type": type,
            "Content": content
        }
        
        if description:
            params["Description"] = description
        
        if tags:
            params["Tags"] = tags
        
        response = connect_client.create_contact_flow(**params)
        
        return {
            "status": "success",
            "contact_flow_id": response["ContactFlowId"],
            "contact_flow_arn": response["ContactFlowArn"],
            "name": name,
            "type": type
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_create_outbound(
    instance_id: str,
    name: str,
    mode: str,
    parameters: Dict[str, Any],
    description: str = "",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create an outbound contact flow using a template.
    
    Supports two modes:
    - PLAY_PROMPT: Static TTS message (no interaction)
    - AI_AGENT: Interactive flow with Lex/Lambda integration
    
    Args:
        instance_id: The ID of the Connect instance
        name: Name for the contact flow
        mode: Mode of operation - "PLAY_PROMPT" or "AI_AGENT"
        parameters: Template parameters for the flow
            For PLAY_PROMPT mode:
                - prompt_text (required): TTS message to play
                - prompt_ssml (optional): SSML version of message
                - campaign_id (optional): Campaign identifier
            For AI_AGENT mode:
                - greeting_message (required): Initial greeting
                - confirmation_question (required): Question to ask
                - lex_bot_arn (required): Lex bot ARN
                - lambda_arn (required): Lambda function ARN
                - (see ai_agent_outbound.json template for full list)
        description: Optional description for the flow
        tags: Optional tags for the contact flow
        
    Returns:
        Dictionary containing the created contact flow ID and ARN
    """
    try:
        # Select template based on mode
        template_map = {
            "PLAY_PROMPT": "play_prompt_outbound",
            "AI_AGENT": "ai_agent_outbound"
        }
        
        if mode.upper() not in template_map:
            return {
                "status": "error",
                "error": f"Invalid mode. Must be one of: {list(template_map.keys())}"
            }
        
        template_name = template_map[mode.upper()]
        
        # Validate and render template
        try:
            validated_params = template_engine.validate_parameters(
                template_name,
                parameters
            )
            rendered_content = template_engine.render(template_name, validated_params)
        except ValueError as ve:
            return {
                "status": "error",
                "error": f"Parameter validation failed: {str(ve)}"
            }
        
        # Create the contact flow
        flow_type = "OUTBOUND_WHISPER_FLOW"
        
        params = {
            "InstanceId": instance_id,
            "Name": name,
            "Type": flow_type,
            "Content": json.dumps(rendered_content)
        }
        
        if description:
            params["Description"] = description
        else:
            params["Description"] = f"Outbound flow ({mode}) created via MCP"
        
        if tags:
            params["Tags"] = tags
        
        response = connect_client.create_contact_flow(**params)
        
        return {
            "status": "success",
            "contact_flow_id": response["ContactFlowId"],
            "contact_flow_arn": response["ContactFlowArn"],
            "name": name,
            "type": flow_type,
            "mode": mode,
            "template_used": template_name,
            "validated_parameters": validated_params
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_update_content(
    instance_id: str,
    contact_flow_id: str,
    content: str
) -> Dict[str, Any]:
    """Update the content of an existing contact flow.
    
    Args:
        instance_id: The ID of the Connect instance
        contact_flow_id: The ID of the contact flow to update
        content: New JSON flow definition as string
        
    Returns:
        Dictionary containing the update status
    """
    try:
        connect_client.update_contact_flow_content(
            InstanceId=instance_id,
            ContactFlowId=contact_flow_id,
            Content=content
        )
        
        return {
            "status": "success",
            "message": f"Contact flow {contact_flow_id} updated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_update_from_template(
    instance_id: str,
    contact_flow_id: str,
    template_name: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Update a contact flow using a template with parameters.
    
    Args:
        instance_id: The ID of the Connect instance
        contact_flow_id: The ID of the contact flow to update
        template_name: Name of the template to use
        parameters: Template parameters
        
    Returns:
        Dictionary containing the update status
    """
    try:
        # Render template
        try:
            validated_params = template_engine.validate_parameters(
                template_name,
                parameters
            )
            rendered_content = template_engine.render(template_name, validated_params)
        except ValueError as ve:
            return {
                "status": "error",
                "error": f"Parameter validation failed: {str(ve)}"
            }
        
        # Update the contact flow
        connect_client.update_contact_flow_content(
            InstanceId=instance_id,
            ContactFlowId=contact_flow_id,
            Content=json.dumps(rendered_content)
        )
        
        return {
            "status": "success",
            "message": f"Contact flow {contact_flow_id} updated from template",
            "template_used": template_name,
            "validated_parameters": validated_params
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_delete(
    instance_id: str,
    contact_flow_id: str
) -> Dict[str, Any]:
    """Delete a contact flow.
    
    Args:
        instance_id: The ID of the Connect instance
        contact_flow_id: The ID of the contact flow to delete
        
    Returns:
        Dictionary containing the deletion status
    """
    try:
        connect_client.delete_contact_flow(
            InstanceId=instance_id,
            ContactFlowId=contact_flow_id
        )
        
        return {
            "status": "success",
            "message": f"Contact flow {contact_flow_id} deleted successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_list_templates(
    category: Optional[str] = None
) -> Dict[str, Any]:
    """List available contact flow templates.
    
    Args:
        category: Optional filter by category (outbound, inbound, shared)
        
    Returns:
        Dictionary containing list of available templates
    """
    try:
        templates = template_registry.list_templates(category=category)
        
        return {
            "status": "success",
            "templates": templates,
            "count": len(templates)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_get_template_schema(
    template_name: str
) -> Dict[str, Any]:
    """Get the parameter schema for a template.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Dictionary containing the JSON schema for template parameters
    """
    try:
        schema = template_registry.get_template_schema(template_name)
        
        return {
            "status": "success",
            "template_name": template_name,
            "schema": schema
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_validate_parameters(
    template_name: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate parameters against a template without creating a flow.
    
    Args:
        template_name: Name of the template to validate against
        parameters: Parameters to validate
        
    Returns:
        Dictionary containing validation results
    """
    try:
        validated = template_engine.validate_parameters(template_name, parameters)
        
        return {
            "status": "success",
            "template_name": template_name,
            "validated_parameters": validated,
            "message": "Parameters are valid"
        }
    except ValueError as ve:
        return {
            "status": "error",
            "error": str(ve),
            "template_name": template_name
        }


@mcp.tool()
def contact_flows_create_version(
    instance_id: str,
    contact_flow_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new version of a contact flow.
    
    Args:
        instance_id: The ID of the Connect instance
        contact_flow_id: The ID of the contact flow
        name: Optional name for the version
        description: Optional description for the version
        
    Returns:
        Dictionary containing the created version details
    """
    try:
        params = {
            "InstanceId": instance_id,
            "ContactFlowId": contact_flow_id
        }
        
        if name:
            params["Name"] = name
        if description:
            params["Description"] = description
        
        response = connect_client.create_contact_flow_version(**params)
        
        return {
            "status": "success",
            "version_id": response.get("ContactFlowVersionId", "latest"),
            "contact_flow_id": contact_flow_id,
            "name": name or "New Version",
            "description": description or ""
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def contact_flows_search(
    instance_id: str,
    search_filter: Optional[Dict[str, Any]] = None,
    max_results: int = 100
) -> Dict[str, Any]:
    """Search contact flows with various filters.
    
    Args:
        instance_id: The ID of the Connect instance
        search_filter: Optional filter criteria
            - name_prefix: Filter by name prefix
            - contact_flow_types: List of flow types
            - states: List of flow states (ACTIVE, ARCHIVED)
        max_results: Maximum number of results
        
    Returns:
        Dictionary containing filtered contact flows
    """
    try:
        # First get all flows
        params = {
            "InstanceId": instance_id,
            "MaxResults": max_results
        }
        
        response = connect_client.list_contact_flows(**params)
        flows = response.get("ContactFlowSummaryList", [])
        
        # Apply filters
        if search_filter:
            if "name_prefix" in search_filter:
                prefix = search_filter["name_prefix"].lower()
                flows = [f for f in flows if f["Name"].lower().startswith(prefix)]
            
            if "contact_flow_types" in search_filter:
                types = search_filter["contact_flow_types"]
                flows = [f for f in flows if f["Type"] in types]
            
            if "states" in search_filter:
                states = search_filter["states"]
                flows = [f for f in flows if f.get("State", "ACTIVE") in states]
        
        return {
            "status": "success",
            "contact_flows": [
                {
                    "id": flow["Id"],
                    "arn": flow["Arn"],
                    "name": flow["Name"],
                    "type": flow["Type"],
                    "state": flow.get("State", "ACTIVE"),
                    "last_modified_time": flow.get("LastModifiedTime")
                }
                for flow in flows
            ],
            "total_count": len(flows)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Export the MCP server
if __name__ == "__main__":
    mcp.run()
