import uuid
from typing import Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from pydantic import BaseModel
from schema import ChatMessage


# === MODELS ESSENTIELS ===

class MessageConversionError(Exception):
    """Raised when message content cannot be converted to string."""
    pass


# === FONCTIONS ESSENTIELLES ===


def remove_tool_calls(content: str | list[str | dict]) -> str | list[str | dict]:
    """Remove tool calls from content."""
    if isinstance(content, str):
        return content
    return [
        content_item
        for content_item in content
        if isinstance(content_item, str) or content_item["type"] != "tool_use"
    ]


def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    """Convert message content to string format."""
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if isinstance(content_item, dict) and content_item.get("type") == "text":
            text.append(content_item.get("text", ""))
    return "".join(text)


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    """Create a ChatMessage from a LangChain message."""
    try:
        match message:
            case HumanMessage():
                return ChatMessage(
                    type="human",
                    content=convert_message_content_to_string(message.content),
                )

            case AIMessage():
                ai_message = ChatMessage(
                    type="ai",
                    content=convert_message_content_to_string(message.content),
                )
                if message.tool_calls:
                    ai_message.tool_calls = message.tool_calls
                if message.response_metadata:
                    ai_message.response_metadata = message.response_metadata
                return ai_message

            case ToolMessage():
                return ChatMessage(
                    type="tool",
                    content=convert_message_content_to_string(message.content),
                    tool_call_id=message.tool_call_id,
                )

            case _:
                raise MessageConversionError(
                    f"Unsupported message type: {message.__class__.__name__}"
                )

    except Exception as e:
        if isinstance(e, MessageConversionError):
            raise
        raise MessageConversionError(f"Failed to convert message: {str(e)}")


# === FONCTIONS MOCK (sans persistance) ===


async def add_message(model, conversation_id, message_request, token):
    """Mock function - no actual saving since no persistence."""
    return {"status": "success", "message": "Message processed locally"}


async def get_user_info(
    token: str, thread_id: Optional[str] = None, run_id: Optional[uuid.UUID] = None
) -> str:
    """Mock function - return simple user info for local development."""
    return "Opérateur"
