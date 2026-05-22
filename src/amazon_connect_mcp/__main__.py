"""Amazon Connect MCP Server - Module Execution Entry Point.

Allows running the server as: python -m amazon_connect_mcp
"""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
