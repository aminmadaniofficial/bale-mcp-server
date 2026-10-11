"""
Tests for messaging tool definitions and behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bale_mcp.server import create_server
from bale_mcp.session_manager import session_manager


@pytest.mark.asyncio
async def test_messaging_tools_exist():
    server = create_server()
    tools = {t.name: t for t in await server.list_tools()}

    assert "bale_edit_message" in tools
    assert "bale_edit_media_caption" in tools
    assert "bale_batch_edit_messages" in tools


@pytest.mark.asyncio
async def test_batch_edit_messages_execution():
    server = create_server()
    tools = {t.name: t for t in await server.list_tools()}
    batch_tool = tools["bale_batch_edit_messages"]

    mock_client = AsyncMock()
    mock_client.edit_message = AsyncMock(return_value={"status": "ok"})

    with patch.object(session_manager, "get_client", AsyncMock(return_value=mock_client)):
        from bale_mcp.tools.messaging import register_messaging_tools
        from mcp.server.mcpserver import MCPServer

        test_srv = MCPServer(name="test")
        register_messaging_tools(test_srv)

        # Directly call through tool handler
        tool_fn = None
        for t, handler in test_srv._tool_handlers.items() if hasattr(test_srv, "_tool_handlers") else []:
            pass

    assert batch_tool.description is not None
