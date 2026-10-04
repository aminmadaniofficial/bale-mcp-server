"""
Core MCP Server implementation for Bale Messenger.
"""

from typing import Literal
import logging
from mcp.server.mcpserver import MCPServer

from bale_mcp.tools.auth import register_auth_tools
from bale_mcp.tools.messaging import register_messaging_tools
from bale_mcp.tools.contacts import register_contacts_tools
from bale_mcp.tools.groups import register_groups_tools
from bale_mcp.tools.reactions import register_reactions_tools
from bale_mcp.config import config

logger = logging.getLogger("bale_mcp.server")


def create_server() -> MCPServer:
    """
    Factory function to initialize and configure the Bale MCP Server with all tools.
    """
    server = MCPServer(
        name="bale-mcp-server",
        instructions=(
            "Bale Messenger MCP Server provides tools to interact with Bale user accounts. "
            "You can manage sessions, list recent dialogs, read chat histories, send and reply to messages, "
            "edit or delete messages, manage contacts, search users, inspect groups, and send reactions."
        ),
    )

    # Register all modular toolsets
    register_auth_tools(server)
    register_messaging_tools(server)
    register_contacts_tools(server)
    register_groups_tools(server)
    register_reactions_tools(server)

    return server


# Default server instance
server = create_server()


def run_server(transport: Literal["stdio", "sse", "streamable-http"] = "stdio", **kwargs) -> None:
    """
    Runs the MCP server using the specified transport protocol.
    """
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info(f"Starting Bale MCP Server with transport: {transport}")
    server.run(transport=transport, **kwargs)
