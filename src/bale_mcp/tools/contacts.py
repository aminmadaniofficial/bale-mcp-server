"""
Contacts and user profile tools for Bale MCP Server.
"""

from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer
from aiobale.enums import ChatType
from bale_mcp.session_manager import session_manager
from bale_mcp.utils import serialize_entity


def register_contacts_tools(server: MCPServer) -> None:
    """Registers contact and profile tools on the MCP server."""

    @server.tool(
        name="bale_get_contacts",
        description="Retrieve the list of saved contacts from the active Bale account.",
    )
    async def bale_get_contacts() -> List[Dict[str, Any]]:
        """
        Retrieves contact list.
        """
        client = await session_manager.get_client()
        try:
            contacts = await client.load_contacts()
            return [serialize_entity(c) for c in contacts]
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool(
        name="bale_search_user",
        description="Search for a Bale user, bot, group, or channel by username or phone number.",
    )
    async def bale_search_user(
        query: str,
    ) -> Dict[str, Any]:
        """
        Searches for a peer by username (e.g. '@durov' or 'durov') or phone number (e.g. '989123456789').

        Args:
            query: Username or phone number in international format without plus.
        """
        client = await session_manager.get_client()
        clean_query = query.strip().lstrip("@")

        try:
            if clean_query.isdigit() and len(clean_query) >= 10:
                user = await client.search_contact(phone_number=clean_query)
                return {"found": user is not None, "type": "user", "result": serialize_entity(user)}

            res = await client.search_username(username=clean_query)
            user = getattr(res, "user", None)
            group = getattr(res, "group", None)

            if user:
                return {"found": True, "type": "user", "result": serialize_entity(user)}
            elif group:
                return {"found": True, "type": "group_or_channel", "result": serialize_entity(group)}

            return {"found": False, "query": query, "message": "No user or group found with this query."}
        except Exception as e:
            return {"found": False, "error": str(e)}

    @server.tool(
        name="bale_get_user_info",
        description="Get detailed profile information (name, about, username, avatar) for a user by user_id.",
    )
    async def bale_get_user_info(
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Fetches full profile information for a user.

        Args:
            user_id: The Bale user ID.
        """
        client = await session_manager.get_client()
        try:
            full_user = await client.load_full_user(chat_id=user_id, chat_type=ChatType.PRIVATE)
            return {"success": True, "user": serialize_entity(full_user)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_import_contacts",
        description="Import one or more contacts by phone number and name into Bale address book.",
    )
    async def bale_import_contacts(
        contacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Imports contacts into your account.

        Args:
            contacts: List of dicts, each with 'phone' (int/str, e.g. 989121234567) and 'name' (str).
        """
        client = await session_manager.get_client()
        prepared_list = []
        for c in contacts:
            phone = int(str(c["phone"]).replace("+", ""))
            name = str(c.get("name", "Contact"))
            prepared_list.append((phone, name))

        try:
            peers = await client.import_contacts(prepared_list)
            return {"success": True, "imported_count": len(peers), "peers": [serialize_entity(p) for p in peers]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_block_user",
        description="Block a user by user ID.",
    )
    async def bale_block_user(user_id: int) -> Dict[str, Any]:
        """
        Blocks the specified user.

        Args:
            user_id: Target user ID to block.
        """
        client = await session_manager.get_client()
        try:
            res = await client.block_user(user_id=user_id)
            return {"success": True, "result": serialize_entity(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_unblock_user",
        description="Unblock a previously blocked user by user ID.",
    )
    async def bale_unblock_user(user_id: int) -> Dict[str, Any]:
        """
        Unblocks the specified user.

        Args:
            user_id: Target user ID to unblock.
        """
        client = await session_manager.get_client()
        try:
            res = await client.unblock_user(user_id=user_id)
            return {"success": True, "result": serialize_entity(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_get_blocked_users",
        description="List all users currently blocked by the active account.",
    )
    async def bale_get_blocked_users() -> List[Dict[str, Any]]:
        """
        Retrieves list of blocked users.
        """
        client = await session_manager.get_client()
        try:
            blocked = await client.load_blocked_users()
            return [serialize_entity(u) for u in blocked]
        except Exception as e:
            return [{"error": str(e)}]
