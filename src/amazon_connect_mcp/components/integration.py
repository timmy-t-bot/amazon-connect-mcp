"""Amazon Connect MCP Server - Components Registration Module.

This module provides a convenient way to register all Connect infrastructure
component tools with an MCP server.

Example:
    from mcp.server.fastmcp import FastMCP
    from amazon_connect_mcp.components.integration import register_components_with_mcp
    
    mcp = FastMCP("amazon_connect")
    register_components_with_mcp(mcp)
"""

from typing import Any, List

from mcp.server.fastmcp import FastMCP

from .instance_manager import (
    connect_instances_list,
    connect_instances_describe,
    connect_instances_update,
    connect_instances_create,
    connect_instances_delete,
)

from .phone_numbers import (
    connect_phone_numbers_search,
    connect_phone_numbers_claim,
    connect_phone_numbers_release,
    connect_phone_numbers_list,
    connect_phone_numbers_describe,
    connect_phone_numbers_update,
)

from .queues import (
    connect_queues_list,
    connect_queues_describe,
    connect_queues_create,
    connect_queues_update,
    connect_queues_delete,
)

from .hours_of_operation import (
    connect_hours_of_operations_list,
    connect_hours_of_operations_describe,
    connect_hours_of_operations_create,
    connect_hours_of_operations_update,
    connect_hours_of_operations_delete,
    connect_hours_of_operations_create_override,
    connect_hours_of_operations_delete_override,
    connect_hours_of_operations_describe_override,
)

from .prompts import (
    connect_prompts_list,
    connect_prompts_describe,
    connect_prompts_create,
    connect_prompts_delete,
)

# List of all component tools for registration
ALL_COMPONENT_TOOLS = [
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
]


def register_components_with_mcp(mcp_server: FastMCP) -> int:
    """Register all Connect component tools with an MCP server.
    
    Args:
        mcp_server: FastMCP server instance
        
    Returns:
        Number of tools registered
        
    Example:
        >>> from mcp.server.fastmcp import FastMCP
        >>> from amazon_connect_mcp.components.integration import register_components_with_mcp
        >>> 
        >>> mcp = FastMCP("amazon_connect")
        >>> count = register_components_with_mcp(mcp)
        >>> print(f"Registered {count} tools")
    """
    registered_count = 0
    
    for tool_func in ALL_COMPONENT_TOOLS:
        mcp_server.tool()(tool_func)
        registered_count += 1
    
    return registered_count


def get_component_tools() -> List[Any]:
    """Get a list of all component tool functions.
    
    Returns:
        List of all component tool functions
        
    Example:
        >>> tools = get_component_tools()
        >>> for tool in tools:
        ...     print(tool.__name__)
    """
    return ALL_COMPONENT_TOOLS.copy()


def get_component_tools_by_category() -> dict:
    """Get component tools organized by category.
    
    Returns:
        Dictionary with categories as keys and tool lists as values
        
    Example:
        >>> categories = get_component_tools_by_category()
        >>> print(f"Instance tools: {len(categories['instances'])}")
    """
    return {
        "instances": [
            connect_instances_list,
            connect_instances_describe,
            connect_instances_update,
            connect_instances_create,
            connect_instances_delete,
        ],
        "phone_numbers": [
            connect_phone_numbers_search,
            connect_phone_numbers_claim,
            connect_phone_numbers_release,
            connect_phone_numbers_list,
            connect_phone_numbers_describe,
            connect_phone_numbers_update,
        ],
        "queues": [
            connect_queues_list,
            connect_queues_describe,
            connect_queues_create,
            connect_queues_update,
            connect_queues_delete,
        ],
        "hours_of_operation": [
            connect_hours_of_operations_list,
            connect_hours_of_operations_describe,
            connect_hours_of_operations_create,
            connect_hours_of_operations_update,
            connect_hours_of_operations_delete,
            connect_hours_of_operations_create_override,
            connect_hours_of_operations_delete_override,
            connect_hours_of_operations_describe_override,
        ],
        "prompts": [
            connect_prompts_list,
            connect_prompts_describe,
            connect_prompts_create,
            connect_prompts_delete,
        ],
    }
