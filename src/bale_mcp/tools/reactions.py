"""
Reactions and presence tools for Bale MCP Server.
"""

from typing import Any, Dict, List
from mcp.server.mcpserver import MCPServer
from aiobale.types import OtherMessage
from aiobale.enums import TypingMode
from bale_mcp.session_manager import session_manager
from bale_mcp.utils import resolve_chat_type, serialize_entity


def register_reactions_tools(server: MCPServer) -> None:
    """Registers reactions and presence indicators on the MCP server."""

    @server.tool(
        name="bale_send_reaction",
        description="Add an emoji reaction (e.g. 👍, ❤️, 🔥) to a specific message in a chat.",
    )
    async def bale_send_reaction(
        chat_id: int,
        message_id: int,
        emoji: str,
        chat_type: str = "private",
    ) -> Dict[str, Any]:
        """
        Adds an emoji reaction to a message.

        Args:
            chat_id: Chat ID where the message is located.
            message_id: ID of the message to react to.
            emoji: Emoji character (e.g. '👍', '❤️', '🔥', '😂').
            chat_type: Chat type ('private', 'group', 'channel').
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        msg_ref = OtherMessage(message_id=message_id, date=0)
        try:
            res = await client.set_reaction(
                emojy=emoji,
                message=msg_ref,
                chat_id=chat_id,
                chat_type=resolved_type,
            )
            return {"success": True, "reactions": serialize_entity(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_remove_reaction",
        description="Remove an emoji reaction from a message in a chat.",
    )
    async def bale_remove_reaction(
        chat_id: int,
        message_id: int,
        emoji: str,
        chat_type: str = "private",
    ) -> Dict[str, Any]:
        """
        Removes an emoji reaction.

        Args:
            chat_id: Chat ID.
            message_id: Message ID.
            emoji: Emoji to remove.
            chat_type: Chat type.
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        msg_ref = OtherMessage(message_id=message_id, date=0)
        try:
            res = await client.remove_reaction(
                emojy=emoji,
                message=msg_ref,
                chat_id=chat_id,
                chat_type=resolved_type,
            )
            return {"success": True, "reactions": serialize_entity(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_send_typing",
        description="Send a typing action indicator to a chat or group.",
    )
    async def bale_send_typing(
        chat_id: int,
        chat_type: str = "private",
    ) -> Dict[str, Any]:
        """
        Triggers typing presence in a chat.

        Args:
            chat_id: Chat ID.
            chat_type: Chat type ('private', 'group').
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        try:
            res = await client.start_typing(
                chat_id=chat_id,
                chat_type=resolved_type,
                typing_mode=TypingMode.TEXT,
            )
            return {"success": True, "result": serialize_entity(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}
