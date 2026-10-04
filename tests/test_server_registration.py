"""
Tests for MCP Server tool registration.
"""

import pytest
from bale_mcp.server import create_server


@pytest.mark.asyncio
async def test_all_tools_registered():
    server = create_server()
    tools = await server.list_tools()

    tool_names = {t.name for t in tools}

    expected_tools = {
        # Auth & Sessions
        "bale_list_sessions",
        "bale_connect_session",
        "bale_get_me",
        "bale_auth_request_code",
        "bale_auth_verify_code",
        "bale_auth_verify_password",
        "bale_disconnect",
        # Messaging
        "bale_get_dialogs",
        "bale_get_chat_history",
        "bale_send_message",
        "bale_edit_message",
        "bale_delete_message",
        "bale_forward_message",
        "bale_mark_chat_read",
        "bale_pin_message",
        # Contacts & Users
        "bale_get_contacts",
        "bale_search_user",
        "bale_get_user_info",
        "bale_import_contacts",
        "bale_block_user",
        "bale_unblock_user",
        "bale_get_blocked_users",
        # Groups & Channels
        "bale_get_group_info",
        "bale_get_group_members",
        "bale_create_group",
        "bale_invite_to_group",
        "bale_get_group_invite_url",
        "bale_leave_group",
        # Reactions & Presence
        "bale_send_reaction",
        "bale_remove_reaction",
        "bale_send_typing",
    }

    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"
    assert len(tools) >= 31

    for t in tools:
        assert t.description, f"Tool {t.name} is missing a description!"
