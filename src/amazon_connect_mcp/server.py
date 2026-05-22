"""Amazon Connect MCP Server - Main Server Entry Point.

This module initializes the FastMCP server and registers all tools
including contact flows, API bridge, and infrastructure components.
"""

import sys
from typing import Any, Dict, Optional

# Ensure src is in path for imports
from pathlib import Path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mcp.server.fastmcp import FastMCP

from .config import get_config, Config
from . import __version__

# Initialize the main MCP server
mcp = FastMCP("amazon-connect")

# Store config reference for tools
mcConfig: Optional[Config] = None


def _get_config() -> Config:
    """Get or load configuration."""
    global mcConfig
    if mcConfig is None:
        mcConfig = get_config()
    return mcConfig


def _register_contact_flow_tools():
    """Register contact flow tools."""
    # Import all decorated tools - the decorators register them with mcp
    try:
        from ..templates.engine import TemplateEngine
        from ..templates.registry import TemplateRegistry
        import boto3
        
        # Initialize AWS client and template components
        connect_client = boto3.client("connect")
        template_engine = TemplateEngine()
        template_registry = TemplateRegistry()
        
        # Import and expose all contact flow tool functions
        from contact_flows.contact_flow_tools import (
            contact_flows_list,
            contact_flows_describe,
            contact_flows_create,
            contact_flows_create_outbound,
            contact_flows_update_content,
            contact_flows_update_from_template,
            contact_flows_delete,
            contact_flows_list_templates,
            contact_flows_get_template_schema,
            contact_flows_validate_parameters,
            contact_flows_create_version,
            contact_flows_search,
        )
        
        # Register all tools with the main MCP server
        mcp.tool()(contact_flows_list)
        mcp.tool()(contact_flows_describe)
        mcp.tool()(contact_flows_create)
        mcp.tool()(contact_flows_create_outbound)
        mcp.tool()(contact_flows_update_content)
        mcp.tool()(contact_flows_update_from_template)
        mcp.tool()(contact_flows_delete)
        mcp.tool()(contact_flows_list_templates)
        mcp.tool()(contact_flows_get_template_schema)
        mcp.tool()(contact_flows_validate_parameters)
        mcp.tool()(contact_flows_create_version)
        mcp.tool()(contact_flows_search)
    except Exception as e:
        print(f"Warning: Failed to register some contact flow tools: {e}", file=sys.stderr)


def _register_api_bridge_tools():
    """Register API bridge tools (Lambda-backed APIs)."""
    cfg = _get_config()
    
    # Only register if bridge is configured
    if not cfg.api_bridge.is_configured():
        return
    
    try:
        from .connect_api_bridge import (
            connect_phone_numbers_search,
            connect_phone_numbers_claim,
            connect_phone_numbers_release,
            connect_phone_numbers_list,
            connect_instances_list,
            connect_instances_describe,
            connect_instances_update,
            connect_queues_list,
            connect_queues_describe,
            connect_queues_create,
            connect_queues_update,
            connect_queues_delete,
            connect_hours_of_operations_list,
            connect_hours_of_operations_describe,
            connect_hours_of_operations_create,
            connect_hours_of_operations_update,
            connect_hours_of_operations_delete,
            connect_hours_of_operations_list_overrides,
            connect_prompts_list,
            connect_prompts_describe,
            connect_prompts_create,
            connect_prompts_delete,
        )
        
        # Phone Number Tools
        mcp.tool()(connect_phone_numbers_search)
        mcp.tool()(connect_phone_numbers_claim)
        mcp.tool()(connect_phone_numbers_release)
        mcp.tool()(connect_phone_numbers_list)
        
        # Instance Tools
        mcp.tool()(connect_instances_list)
        mcp.tool()(connect_instances_describe)
        mcp.tool()(connect_instances_update)
        
        # Queue Tools
        mcp.tool()(connect_queues_list)
        mcp.tool()(connect_queues_describe)
        mcp.tool()(connect_queues_create)
        mcp.tool()(connect_queues_update)
        mcp.tool()(connect_queues_delete)
        
        # Hours of Operation Tools
        mcp.tool()(connect_hours_of_operations_list)
        mcp.tool()(connect_hours_of_operations_describe)
        mcp.tool()(connect_hours_of_operations_create)
        mcp.tool()(connect_hours_of_operations_update)
        mcp.tool()(connect_hours_of_operations_delete)
        mcp.tool()(connect_hours_of_operations_list_overrides)
        
        # Prompt Tools
        mcp.tool()(connect_prompts_list)
        mcp.tool()(connect_prompts_describe)
        mcp.tool()(connect_prompts_create)
        mcp.tool()(connect_prompts_delete)
        
    except Exception as e:
        print(f"Warning: Failed to register API bridge tools: {e}", file=sys.stderr)


def _register_component_tools():
    """Register infrastructure component tools (direct boto3)."""
    try:
        from .components import (
            # Instances
            connect_instances_list,
            connect_instances_describe,
            connect_instances_update,
            connect_instances_create,
            connect_instances_delete,
            # Phone Numbers
            connect_phone_numbers_search,
            connect_phone_numbers_claim,
            connect_phone_numbers_release,
            connect_phone_numbers_list,
            connect_phone_numbers_describe,
            connect_phone_numbers_update,
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
            connect_hours_of_operations_create_override,
            connect_hours_of_operations_delete_override,
            connect_hours_of_operations_describe_override,
            # Prompts
            connect_prompts_list,
            connect_prompts_describe,
            connect_prompts_create,
            connect_prompts_delete,
        )
        
        # Instance Tools
        mcp.tool()(connect_instances_list)
        mcp.tool()(connect_instances_describe)
        mcp.tool()(connect_instances_update)
        mcp.tool()(connect_instances_create)
        mcp.tool()(connect_instances_delete)
        
        # Phone Number Tools
        mcp.tool()(connect_phone_numbers_search)
        mcp.tool()(connect_phone_numbers_claim)
        mcp.tool()(connect_phone_numbers_release)
        mcp.tool()(connect_phone_numbers_list)
        mcp.tool()(connect_phone_numbers_describe)
        mcp.tool()(connect_phone_numbers_update)
        
        # Queue Tools
        mcp.tool()(connect_queues_list)
        mcp.tool()(connect_queues_describe)
        mcp.tool()(connect_queues_create)
        mcp.tool()(connect_queues_update)
        mcp.tool()(connect_queues_delete)
        
        # Hours of Operation Tools
        mcp.tool()(connect_hours_of_operations_list)
        mcp.tool()(connect_hours_of_operations_describe)
        mcp.tool()(connect_hours_of_operations_create)
        mcp.tool()(connect_hours_of_operations_update)
        mcp.tool()(connect_hours_of_operations_delete)
        mcp.tool()(connect_hours_of_operations_create_override)
        mcp.tool()(connect_hours_of_operations_delete_override)
        mcp.tool()(connect_hours_of_operations_describe_override)
        
        # Prompt Tools
        mcp.tool()(connect_prompts_list)
        mcp.tool()(connect_prompts_describe)
        mcp.tool()(connect_prompts_create)
        mcp.tool()(connect_prompts_delete)
        
    except Exception as e:
        print(f"Warning: Failed to register component tools: {e}", file=sys.stderr)


def _register_tools():
    """Register all tools with the MCP server."""
    # Register in order of priority
    _register_contact_flow_tools()
    _register_component_tools()  # Prefer direct boto3 over API bridge
    _register_api_bridge_tools()  # Bridge for extended APIs


# Export the registration function for external use
def register_all_tools():
    """Explicitly register all tools.
    
    Called automatically on module import, but can be called
    again if needed after module reloads.
    """
    _register_tools()


@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """Get information about the MCP server.
    
    Returns:
        Dictionary with server info including:
        - name: Server name
        - version: Server version
        - config: Basic configuration (without secrets)
    """
    cfg = _get_config()
    
    return {
        "name": "amazon-connect-mcp",
        "version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "transport": cfg.mcp.transport,
        "aws_region": cfg.aws.region,
        "api_bridge_enabled": cfg.api_bridge.is_configured(),
        "connect_instance_id": cfg.connect.instance_id if cfg.connect.instance_id else None,
    }


# Register all tools on module import
_register_tools()


if __name__ == "__main__":
    # Run the server
    mcp.run()
