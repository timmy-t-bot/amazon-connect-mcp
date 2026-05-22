"""Amazon Connect MCP Server - Infrastructure Components Module.

This module provides MCP tools for managing Amazon Connect infrastructure components:
- Instance management (create, describe, update, delete instances)
- Phone numbers (search, claim, release, list)
- Queues (create, update, delete, describe, list)
- Hours of Operation (create, update, delete, describe, list, overrides)
- Prompts (create, delete, describe, list)

Usage:
    from amazon_connect_mcp.components import (
        connect_instances_list,
        connect_instances_describe,
        connect_phone_numbers_search,
        connect_queues_create,
        connect_hours_of_operations_create,
        connect_prompts_create,
    )
"""

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

__all__ = [
    # Instances
    "connect_instances_list",
    "connect_instances_describe",
    "connect_instances_update",
    "connect_instances_create",
    "connect_instances_delete",
    # Phone Numbers
    "connect_phone_numbers_search",
    "connect_phone_numbers_claim",
    "connect_phone_numbers_release",
    "connect_phone_numbers_list",
    "connect_phone_numbers_describe",
    "connect_phone_numbers_update",
    # Queues
    "connect_queues_list",
    "connect_queues_describe",
    "connect_queues_create",
    "connect_queues_update",
    "connect_queues_delete",
    # Hours of Operation
    "connect_hours_of_operations_list",
    "connect_hours_of_operations_describe",
    "connect_hours_of_operations_create",
    "connect_hours_of_operations_update",
    "connect_hours_of_operations_delete",
    "connect_hours_of_operations_create_override",
    "connect_hours_of_operations_delete_override",
    "connect_hours_of_operations_describe_override",
    # Prompts
    "connect_prompts_list",
    "connect_prompts_describe",
    "connect_prompts_create",
    "connect_prompts_delete",
]
