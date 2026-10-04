"""
Unit tests for Bale MCP utilities.
"""

from aiobale.enums import ChatType
from bale_mcp.utils import resolve_chat_type, serialize_entity, format_message_summary


def test_resolve_chat_type():
    assert resolve_chat_type("private") == ChatType.PRIVATE
    assert resolve_chat_type("pv") == ChatType.PRIVATE
    assert resolve_chat_type("direct") == ChatType.PRIVATE
    assert resolve_chat_type("group") == ChatType.GROUP
    assert resolve_chat_type("supergroup") == ChatType.SUPER_GROUP
    assert resolve_chat_type("super_group") == ChatType.SUPER_GROUP
    assert resolve_chat_type("channel") == ChatType.CHANNEL
    assert resolve_chat_type("bot") == ChatType.BOT
    assert resolve_chat_type(1) == ChatType.PRIVATE
    assert resolve_chat_type(2) == ChatType.GROUP
    assert resolve_chat_type(ChatType.CHANNEL) == ChatType.CHANNEL


def test_serialize_entity():
    data = {
        "str": "hello",
        "int": 42,
        "enum": ChatType.PRIVATE,
        "nested": {"key": "val"},
        "list": [1, 2, ChatType.GROUP],
    }
    serialized = serialize_entity(data)
    assert serialized["str"] == "hello"
    assert serialized["int"] == 42
    assert serialized["enum"] == 1
    assert serialized["nested"]["key"] == "val"
    assert serialized["list"] == [1, 2, 2]


def test_format_message_summary():
    class DummyChat:
        id = 12345

    class DummyMessage:
        chat = DummyChat()
        sender_id = 999
        message_id = 777
        text = "Test message"
        date = 1680000000
        reply_to_message = None
        document = None
        photo = None

    summary = format_message_summary(DummyMessage())
    assert summary["chat_id"] == 12345
    assert summary["sender_id"] == 999
    assert summary["message_id"] == 777
    assert summary["text"] == "Test message"
    assert summary["date"] == 1680000000
