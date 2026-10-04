"""
Group and channel management tools for Bale MCP Server.
"""

from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer
from aiobale.enums import GroupType
from bale_mcp.session_manager import session_manager
from bale_mcp.utils import serialize_entity


def register_groups_tools(server: MCPServer) -> None:
    """Registers group and channel management tools on the MCP server."""

    @server.tool(
        name="bale_get_group_info",
        description="Retrieve full information, settings, member count, and permissions for a group or channel.",
    )
    async def bale_get_group_info(
        group_id: int,
    ) -> Dict[str, Any]:
        """
        Fetches detailed information about a group or channel.

        Args:
            group_id: The group or channel ID.
        """
        client = await session_manager.get_client()
        try:
            full_group = await client.get_full_group(chat_id=group_id)
            return {"success": True, "group": serialize_entity(full_group)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_get_group_members",
        description="Retrieve the list of members in a group or channel.",
    )
    async def bale_get_group_members(
        group_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves group members.

        Args:
            group_id: The group ID.
            limit: Maximum members to return (default 50).
        """
        client = await session_manager.get_client()
        members = await client.load_members(chat_id=group_id, limit=limit)
        return [serialize_entity(m) for m in members]

    @server.tool(
        name="bale_create_group",
        description="Create a new group or channel on Bale with initial members.",
    )
    async def bale_create_group(
        title: str,
        user_ids: Optional[List[int]] = None,
        is_channel: bool = False,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a new group or channel.

        Args:
            title: Title/name of the group or channel.
            user_ids: Optional list of user IDs to add initially.
            is_channel: Set to True to create a broadcast Channel; otherwise creates a Group.
            username: Optional public @username for public groups/channels.
        """
        client = await session_manager.get_client()
        target_type = GroupType.CHANNEL if is_channel else GroupType.GROUP
        users_tuple = tuple(user_ids or [])

        res = await client.create_group(
            title=title,
            username=username,
            users=users_tuple,
            group_type=target_type,
        )

        return {"success": True, "result": serialize_entity(res)}

    @server.tool(
        name="bale_invite_to_group",
        description="Invite one or more users to an existing group or channel.",
    )
    async def bale_invite_to_group(
        group_id: int,
        user_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Invites users to a group.

        Args:
            group_id: The group ID.
            user_ids: List of user IDs to invite.
        """
        client = await session_manager.get_client()
        res = await client.invite_users(chat_id=group_id, users=user_ids)
        return {"success": True, "result": serialize_entity(res)}

    @server.tool(
        name="bale_get_group_invite_url",
        description="Get the permanent invitation link (URL) for a group or channel.",
    )
    async def bale_get_group_invite_url(
        group_id: int,
    ) -> Dict[str, Any]:
        """
        Fetches the invite URL for a group.

        Args:
            group_id: Target group ID.
        """
        client = await session_manager.get_client()
        try:
            url = await client.get_group_invite_url(chat_id=group_id)
            return {"success": True, "url": getattr(url, "url", str(url))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_leave_group",
        description="Leave a group or channel.",
    )
    async def bale_leave_group(
        group_id: int,
    ) -> Dict[str, Any]:
        """
        Leaves a group.

        Args:
            group_id: Group ID to leave.
        """
        client = await session_manager.get_client()
        res = await client.leave_group(chat_id=group_id)
        return {"success": True, "result": serialize_entity(res)}
