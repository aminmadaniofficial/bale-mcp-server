"""
Utility functions for type resolution, normalization, and serialization.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from aiobale.enums import ChatType


def resolve_chat_type(val: Union[str, int, ChatType]) -> ChatType:
    """
    Normalizes string, integer, or ChatType enum into aiobale ChatType.
    Supports flexible naming commonly produced by LLMs.
    """
    if isinstance(val, ChatType):
        return val

    if isinstance(val, int):
        try:
            return ChatType(val)
        except ValueError:
            return ChatType.PRIVATE

    val_str = str(val).strip().lower().replace("-", "_").replace(" ", "_")

    mapping = {
        "private": ChatType.PRIVATE,
        "direct": ChatType.PRIVATE,
        "pv": ChatType.PRIVATE,
        "user": ChatType.PRIVATE,
        "person": ChatType.PRIVATE,
        "group": ChatType.GROUP,
        "supergroup": ChatType.SUPER_GROUP,
        "super_group": ChatType.SUPER_GROUP,
        "channel": ChatType.CHANNEL,
        "bot": ChatType.BOT,
        "unknown": ChatType.UNKNOWN,
    }

    return mapping.get(val_str, ChatType.PRIVATE)


def serialize_entity(obj: Any) -> Any:
    """
    Recursively serialize Pydantic models, Enums, and complex Python types
    into JSON-serializable dictionaries and primitives.
    """
    if obj is None:
        return None

    if isinstance(obj, (int, float, str, bool)):
        return obj

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, (list, tuple, set)):
        return [serialize_entity(item) for item in obj]

    if isinstance(obj, dict):
        return {str(k): serialize_entity(v) for k, v in obj.items()}

    if hasattr(obj, "model_dump"):
        try:
            return serialize_entity(obj.model_dump(mode="json"))
        except Exception:
            return serialize_entity(obj.model_dump())

    if hasattr(obj, "dict"):
        return serialize_entity(obj.dict())

    if hasattr(obj, "__dict__"):
        clean_dict = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return serialize_entity(clean_dict)

    return str(obj)


def format_message_summary(msg: Any) -> Dict[str, Any]:
    """
    Extracts a concise, high-signal summary of a Message for LLM consumption.
    """
    if not msg:
        return {}

    chat_id = getattr(getattr(msg, "chat", None), "id", None)
    sender_id = getattr(msg, "sender_id", None)
    message_id = getattr(msg, "message_id", None)
    text = getattr(msg, "text", "") or ""
    date = getattr(msg, "date", None)
    reply_to = getattr(getattr(msg, "reply_to_message", None), "message_id", None)

    # If text is empty, check for caption in document or photo
    if not text:
        doc = getattr(msg, "document", None)
        photo = getattr(msg, "photo", None)
        if doc and getattr(doc, "caption", None):
            cap = doc.caption
            text = getattr(cap, "content", str(cap)) if hasattr(cap, "content") else str(cap)
        elif photo and getattr(photo, "caption", None):
            cap = photo.caption
            text = getattr(cap, "content", str(cap)) if hasattr(cap, "content") else str(cap)

    summary: Dict[str, Any] = {
        "message_id": message_id,
        "chat_id": chat_id,
        "sender_id": sender_id,
        "text": text,
        "date": date,
    }

    if reply_to:
        summary["reply_to_message_id"] = reply_to

    if getattr(msg, "document", None):
        doc = msg.document
        summary["attachment"] = {
            "type": "document",
            "file_name": getattr(doc, "name", None),
            "file_size": getattr(doc, "file_size", None),
            "mime_type": getattr(doc, "mime_type", None),
        }
    elif getattr(msg, "photo", None):
        summary["attachment"] = {
            "type": "photo",
            "caption": getattr(msg, "caption", ""),
        }

    return summary
