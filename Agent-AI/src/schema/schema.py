from typing import Any, Literal, NotRequired

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class AgentInfo(BaseModel):
    """Info about an available agent."""

    key: str = Field(
        description="Agent key.",
        examples=["research-assistant"],
    )
    description: str = Field(
        description="Description of the agent.",
        examples=["A research assistant for generating research papers."],
    )


class ToolCall(TypedDict):
    """Represents a request to call a tool."""

    name: str
    """The name of the tool to be called."""
    args: dict[str, Any]
    """The arguments to the tool call."""
    id: str | None
    """An identifier associated with the tool call."""
    type: NotRequired[Literal["tool_call"]]


class ChatMessage(BaseModel):
    type: Literal["human", "ai", "tool", "custom"] = Field(
        description="Role of the message.",
        examples=["human", "ai", "tool", "custom"],
    )
    content: str = Field(
        description="Content of the message.",
        examples=["Hello, world!"],
    )
    tool_calls: list[ToolCall] = Field(
        description="Tool calls in the message.",
        default=[],
    )
    tool_call_id: str | None = Field(
        description="Tool call that this message is responding to.",
        default=None,
        examples=["call_Jja7J89XsjrOLA5r!MEOW!SL"],
    )
    thread_id: str | None = Field(
        description="Thread ID of the conversation.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    run_id: str | None = Field(
        description="Run ID of the message.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    response_metadata: dict[str, Any] = Field(
        description="Response metadata. For example: response headers, logprobs, token counts.",
        default={},
    )
    custom_data: dict[str, Any] = Field(
        description="Custom message data.",
        default={},
    )

    def pretty_repr(self) -> str:
        """Get a pretty representation of the message."""
        base_title = self.type.title() + " Message"
        padded = " " + base_title + " "
        sep_len = (80 - len(padded)) // 2
        sep = "=" * sep_len
        second_sep = sep + "=" if len(padded) % 2 else sep
        title = f"{sep}{padded}{second_sep}"
        return f"{title}\n\n{self.content}"

    def pretty_print(self) -> None:
        print(self.pretty_repr())


class UserInput(BaseModel):
    message: str = Field(
        description="User message.",
        examples=["Hello, how are you?"],
    )
    thread_id: str | None = Field(
        description="Thread ID for the conversation.",
        default=None,
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class AgentResponse(BaseModel):
    """Response from agent invocation."""

    content: str = Field(
        description="Content of the agent's response.",
        examples=["I've found the information you requested."],
    )
    thread_id: str = Field(
        description="ID of the conversation thread.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    run_id: str = Field(
        description="ID of the execution run.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
