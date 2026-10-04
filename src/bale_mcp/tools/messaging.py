"""
Messaging and conversation tools for Bale MCP Server.
"""

from typing import Any, Dict, List, Optional, Union
from mcp.server.mcpserver import MCPServer
from aiobale.types import InfoMessage, Peer, IntValue
from bale_mcp.session_manager import session_manager
from bale_mcp.utils import resolve_chat_type, format_message_summary, serialize_entity


def register_messaging_tools(server: MCPServer) -> None:
    """Registers messaging and dialog management tools on the MCP server."""

    @server.tool(
        name="bale_get_dialogs",
        description="Retrieve the list of recent chats, groups, and channels (dialogs) with unread counts and last message previews.",
    )
    async def bale_get_dialogs(
        limit: int = 30,
        exclude_pinned: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetches user dialogs/conversations.

        Args:
            limit: Maximum number of dialogs to return (default 30).
            exclude_pinned: Whether to exclude pinned dialogs.
        """
        client = await session_manager.get_client()
        dialogs = await client.load_dialogs(limit=limit, exclude_pinned=exclude_pinned)

        results: List[Dict[str, Any]] = []
        for d in dialogs:
            peer = getattr(d, "peer", None)
            peer_id = getattr(peer, "id", None)
            peer_type_raw = getattr(peer, "type", None)
            unread_count = getattr(d, "unread_count", 0)
            top_message = getattr(d, "top_message", None)

            item: Dict[str, Any] = {
                "chat_id": peer_id,
                "peer_type": getattr(peer_type_raw, "name", str(peer_type_raw)),
                "unread_count": unread_count,
            }

            if top_message:
                item["last_message"] = format_message_summary(top_message)

            results.append(item)

        return results

    @server.tool(
        name="bale_get_chat_history",
        description="Fetch recent message history from a specific chat, group, or channel.",
    )
    async def bale_get_chat_history(
        chat_id: int,
        chat_type: str = "private",
        limit: int = 25,
        offset_date: int = -1,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves message history.

        Args:
            chat_id: The target chat, user, or group ID.
            chat_type: Chat type ('private', 'group', 'channel', or 'supergroup'). Default is 'private'.
            limit: Number of messages to retrieve (default 25).
            offset_date: Pagination timestamp offset (-1 for latest).
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        messages = await client.load_history(
            chat_id=chat_id,
            chat_type=resolved_type,
            limit=limit,
            offset_date=offset_date,
        )

        return [format_message_summary(msg) for msg in messages]

    @server.tool(
        name="bale_send_message",
        description="Send a text message to a user, group, or channel with optional reply support.",
    )
    async def bale_send_message(
        chat_id: int,
        text: str,
        chat_type: str = "private",
        reply_to_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Sends a message to the specified chat.

        Args:
            chat_id: Target user, group, or channel ID.
            text: Message body to send.
            chat_type: Chat type ('private', 'group', 'channel'). Default is 'private'.
            reply_to_message_id: Optional ID of the message to reply to.
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        reply_to_obj = None
        if reply_to_message_id is not None:
            peer_type = client._resolve_peer_type(resolved_type)
            reply_to_obj = InfoMessage(
                peer=Peer(type=peer_type, id=chat_id),
                message_id=reply_to_message_id,
                date=IntValue(value=0),
            )

        res = await client.send_message(
            text=text,
            chat_id=chat_id,
            chat_type=resolved_type,
            reply_to=reply_to_obj,
        )

        if isinstance(res, list):
            return {
                "success": True,
                "messages": [format_message_summary(m) for m in res]
            }

        return {
            "success": True,
            "message": format_message_summary(res)
        }

    @server.tool(
        name="bale_edit_message",
        description="Edit an existing text message sent previously in a chat.",
    )
    async def bale_edit_message(
        chat_id: int,
        message_id: int,
        new_text: str,
        chat_type: str = "private",
    ) -> Dict[str, Any]:
        """
        Edits an existing message.

        Args:
            chat_id: Chat ID containing the message.
            message_id: The ID of the message to update.
            new_text: New text content for the message.
            chat_type: Chat type ('private', 'group', 'channel'). Default is 'private'.
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        res = await client.edit_message(
            text=new_text,
            message_id=message_id,
            chat_id=chat_id,
            chat_type=resolved_type,
        )

        return {"success": True, "result": serialize_entity(res)}

    @server.tool(
        name="bale_delete_message",
        description="Delete a message from a chat.",
    )
    async def bale_delete_message(
        chat_id: int,
        message_id: int,
        chat_type: str = "private",
        just_me: bool = False,
    ) -> Dict[str, Any]:
        """
        Deletes a message.

        Args:
            chat_id: Chat ID containing the message.
            message_id: Message ID to delete.
            chat_type: Chat type ('private', 'group', 'channel').
            just_me: If True, delete only for current user; otherwise delete for everyone if allowed.
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        res = await client.delete_message(
            message_id=message_id,
            message_date=0,
            chat_id=chat_id,
            chat_type=resolved_type,
            just_me=just_me,
        )

        return {"success": True, "result": serialize_entity(res)}

    @server.tool(
        name="bale_forward_message",
        description="Forward an existing message to another chat or user.",
    )
    async def bale_forward_message(
        from_chat_id: int,
        from_chat_type: str,
        message_id: int,
        to_chat_id: int,
        to_chat_type: str = "private",
    ) -> Dict[str, Any]:
        """
        Forwards a message from one chat to another.

        Args:
            from_chat_id: Source chat ID.
            from_chat_type: Source chat type ('private', 'group', 'channel').
            message_id: ID of the message to forward.
            to_chat_id: Target destination chat ID.
            to_chat_type: Target chat type ('private', 'group', 'channel').
        """
        client = await session_manager.get_client()
        src_type = resolve_chat_type(from_chat_type)
        dst_type = resolve_chat_type(to_chat_type)

        peer_type = client._resolve_peer_type(src_type)
        info_msg = InfoMessage(
            peer=Peer(type=peer_type, id=from_chat_id),
            message_id=message_id,
            date=IntValue(value=0),
        )

        res = await client.forward_message(
            message=info_msg,
            chat_id=to_chat_id,
            chat_type=dst_type,
        )

        return {"success": True, "result": serialize_entity(res)}

    @server.tool(
        name="bale_mark_chat_read",
        description="Mark all messages in a chat or group as read (seen).",
    )
    async def bale_mark_chat_read(
        chat_id: int,
        chat_type: str = "private",
    ) -> Dict[str, Any]:
        """
        Marks incoming messages in the chat as read.

        Args:
            chat_id: Chat ID to mark as read.
            chat_type: Chat type ('private', 'group', 'channel').
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        res = await client.seen_chat(chat_id=chat_id, chat_type=resolved_type)
        return {"success": True, "result": serialize_entity(res)}

    @server.tool(
        name="bale_pin_message",
        description="Pin a message in a private chat or group.",
    )
    async def bale_pin_message(
        chat_id: int,
        message_id: int,
        chat_type: str = "private",
        just_me: bool = False,
    ) -> Dict[str, Any]:
        """
        Pins a message.

        Args:
            chat_id: Chat ID.
            message_id: Message ID to pin.
            chat_type: Chat type ('private', 'group').
            just_me: If True, pin only for current user.
        """
        client = await session_manager.get_client()
        resolved_type = resolve_chat_type(chat_type)

        res = await client.pin_message(
            message_id=message_id,
            message_date=0,
            chat_id=chat_id,
            chat_type=resolved_type,
            just_me=just_me,
        )

        return {"success": True, "result": serialize_entity(res)}
