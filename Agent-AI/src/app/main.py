"""
FastAPI backend for GenAI agent applications.

This module serves as the main entry point for the FastAPI application,
setting up routes, middleware, and application lifecycle management.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict
from uuid import UUID, uuid4

from agents.agents import get_agent, get_all_agent_info
from agents.Agent_AI.prompt.models import CustomState
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from schema import AgentResponse, UserInput

# Logging system removed for simplicity
from app.utils import (
    add_message,
    convert_message_content_to_string,
    get_user_info,
    langchain_to_chat_message,
    remove_tool_calls,
)

# Configure logging with proper format
# Constants
API_VERSION = "0.1.0"
API_TITLE = "GenAI Agent API"
API_DESCRIPTION = "FastAPI backend for GenAI agent applications"


# Custom exception types
class AgentError(Exception):
    """Base exception for agent-related errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class AgentExecutionError(AgentError):
    """Exception raised when agent execution fails."""

    pass


class DatabaseInitializationError(AgentError):
    """Exception raised when database initialization fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Middleware and lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan avec mémoire en mémoire.
    L'agent maintient la conversation dans la mémoire en utilisant les thread_id.
    """
    try:
        # L'agent utilise maintenant InMemorySaver pour la persistance des conversations
        # Les conversations sont maintenues en mémoire par thread_id
        yield
    except Exception as e:
        # Gestion des erreurs simplifiée
        raise DatabaseInitializationError(f"Failed to initialize application: {str(e)}")


async def exception_handler(request: Request, exc: AgentError) -> JSONResponse:
    """
    Global exception handler for agent-related errors.

    Args:
        request: The incoming request
        exc: The caught exception

    Returns:
        JSONResponse: A formatted error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message, "path": request.url.path},
    )


# Application setup
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance
    """
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    app.add_exception_handler(AgentError, exception_handler)

    return app


# Route handlers
async def _handle_input(
    user_input: UserInput, agent: CompiledStateGraph, agent_context: dict[str, Any]
) -> tuple[dict[str, Any], UUID, str]:
    """
    Parse user input and handle any required interrupt resumption.

    Args:
        user_input: The user input to process
        agent: The agent graph to execute
        agent_context: Additional context information to pass to the agent (e.g., bearer token)

    Returns:
        Tuple containing:
        - kwargs for agent invocation
        - run_id for tracking the execution
        - thread_id for conversation tracking

    Raises:
        AgentError: If there's an error processing the input
    """
    try:
        run_id = uuid4()
        thread_id = user_input.thread_id or str(uuid4())
        # Processing input

        configurable = {"thread_id": thread_id, "__bearer_token": agent_context.get("bearer_token")}
        config = RunnableConfig(
            configurable=configurable,
            run_id=run_id,
        )

        input_data = {
            "messages": [HumanMessage(content=user_input.message)],
        }

        kwargs = {
            "input": input_data,
            "config": config,
        }

        return (
            kwargs,
            run_id,
            thread_id,
        )

    except Exception as e:
        # Error processing input
        raise AgentError(f"Failed to process input: {str(e)}")


# Router setup - No authentication required
router = APIRouter()


@router.post("/{agent_id}/invoke", response_model=AgentResponse)
async def invoke(
    user_input: UserInput,
    agent_id: str,
) -> dict:
    """
    Invoke an agent with the given input.

    Args:
        user_input: The input from the user
        agent_id: The ID of the agent to invoke

    Returns:
        AgentResponse: A response containing content, thread_id, and run_id

    Raises:
        HTTPException: If there's an error during execution
    """
    try:
        agent: CompiledStateGraph = get_agent(agent_id)
        kwargs, run_id, thread_id = await _handle_input(
            user_input, agent, {"bearer_token": "mock_token"}
        )

        # Get mock user info since we're working without authentication
        user_info = await get_user_info("mock_token", thread_id=thread_id, run_id=run_id)

        # Add user info to the state
        now_utc = datetime.now(timezone.utc)
        formatted_date = now_utc.strftime("%A, %B %d, %Y %I:%M %p")

        # Create state without accessing database (no conversation history)
        state = CustomState(
            user_info=user_info,
            today_date=formatted_date,
            messages=kwargs["input"]["messages"],  # Only current message, no history
        )
        kwargs["input"] = state


        try:
            # Invoking agent
            response_events = await agent.ainvoke(**kwargs, stream_mode=["updates", "values"])

            if not response_events:
                raise AgentExecutionError("No response received from agent")

            response_type, response = response_events[-1]

            if response_type == "values":
                # Agent completed successfully
                output = langchain_to_chat_message(response["messages"][-1])
            elif response_type == "updates" and "__interrupt__" in response:
                # Agent interrupted
                output = langchain_to_chat_message(
                    AIMessage(content=response["__interrupt__"][0].value)
                )
            else:
                raise AgentExecutionError(f"Unexpected response type: {response_type}")

            # Return only the required fields
            return {"content": output.content, "thread_id": thread_id, "run_id": str(run_id)}

        except asyncio.CancelledError:
            # Handle cancellation
            return {
                "content": "Generation was stopped.",
                "thread_id": thread_id,
                "run_id": str(run_id),
            }
        finally:
            # Cleanup simplified - no task tracking needed
            pass

    except AgentError:
        raise
    except Exception as e:
        # Unexpected error
        raise AgentError(
            "An unexpected error occurred", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Type definitions for SSE messages
class SSEMessageBase(TypedDict):
    type: str
    content: str | dict | None


class ThreadInfo(TypedDict, total=False):
    thread_id: str


class SSEStreamStartMessage(SSEMessageBase):
    type: Literal["stream_start"]
    content: None


class SSETokenMessage(SSEMessageBase):
    type: Literal["stream_token"]
    content: dict


class SSEStreamEndMessage(SSEMessageBase):
    type: Literal["stream_end"]
    content: ThreadInfo | None


class SSEToolExecutionMessage(SSEMessageBase):
    type: Literal["tool_execution_start"]
    content: dict


class SSEToolExecutionCompleteMessage(SSEMessageBase):
    type: Literal["tool_execution_complete"]
    content: dict


class SSEToolExecutionErrorMessage(SSEMessageBase):
    type: Literal["tool_execution_error"]
    content: dict


class SSEErrorMessage(SSEMessageBase):
    type: Literal["error"]
    content: str


SSEMessage = (
    SSEStreamStartMessage
    | SSETokenMessage
    | SSEStreamEndMessage
    | SSEToolExecutionMessage
    | SSEToolExecutionCompleteMessage
    | SSEToolExecutionErrorMessage
    | SSEErrorMessage
)


def create_sse_data(message: SSEMessage) -> str:
    """
    Create a properly formatted SSE data string.

    Args:
        message: The message to format as SSE data

    Returns:
        str: Formatted SSE data string
    """
    event_type = message["type"]
    content = message["content"]
    result = f"event: {event_type}\n"
    if content is not None:
        result += f"data: {json.dumps(content)}\n"
    return result + "\n"


async def process_stream_updates(
    event: dict,
    run_id: UUID,
    thread_id: str,
    user_input: str,
    tool_executions: dict,
    stream_started: bool,
    completed_tools: list = None,  # Track completed tools
) -> AsyncGenerator[tuple[str, bool], None]:
    """
    Process stream updates from the agent and yield SSE messages.

    Args:
        event: The event data from the agent
        run_id: The current run ID
        thread_id: The current thread ID
        user_input: The original user input message
        tool_executions: Dictionary to track tool executions
        stream_started: Whether the stream has started
        completed_tools: List to track completed tools (optional)

    Yields:
        Tuple of (SSE message string, updated stream_started flag)
    """
    if completed_tools is None:
        completed_tools = []
    for node, updates in event.items():
        if node == "__interrupt__":
            for interrupt in updates:
                if not stream_started and interrupt.content:  # Only start stream if there's content
                    yield create_sse_data({"type": "stream_start", "content": None}), True
                    stream_started = True
                yield (
                    create_sse_data(
                        {"type": "stream_token", "content": {"token": interrupt.content}}
                    ),
                    stream_started,
                )
            continue

        # Handle messages
        update_messages = updates.get("messages", [])
        for message in update_messages:
            try:
                chat_message = langchain_to_chat_message(message)
                chat_message.run_id = str(run_id)
                chat_message.thread_id = thread_id

                # Skip re-sending the input message
                if chat_message.type == "human" and chat_message.content == user_input:
                    continue

                # Handle tool calls
                if chat_message.tool_calls:
                    for tool_call in chat_message.tool_calls:
                        # Store tool execution details
                        tool_executions[tool_call["id"]] = {
                            "name": tool_call["name"],
                            "params": tool_call["args"],
                        }
                        
                        yield (
                            create_sse_data(
                                {
                                    "type": "tool_execution_start",
                                    "content": {
                                        "name": tool_call["name"],
                                        "params": tool_call["args"],
                                    },
                                }
                            ),
                            stream_started,
                        )  # Don't change stream_started for tool events
                elif chat_message.type == "tool":
                    # This is a tool response
                    tool_id = chat_message.tool_call_id
                    if tool_id in tool_executions:
                        tool_info = tool_executions.pop(tool_id)  # Remove from tracking
                        
                        completed_tools.append(tool_info["name"])
                        yield (
                            create_sse_data(
                                {
                                    "type": "tool_execution_complete",
                                    "content": {
                                        "name": tool_info["name"],
                                        "params": tool_info["params"],
                                    },
                                }
                            ),
                            stream_started,
                        )  # Don't change stream_started for tool events
                else:
                    # Regular message content
                    if chat_message.content:  # Only process if there's actual content
                        if not stream_started:
                            yield create_sse_data({"type": "stream_start", "content": None}), True
                            stream_started = True
                        yield (
                            create_sse_data(
                                {"type": "stream_token", "content": {"token": chat_message.content}}
                            ),
                            stream_started,
                        )
            except Exception as e:
                # Error parsing message
                if not stream_started:
                    yield create_sse_data({"type": "stream_start", "content": None}), True
                    stream_started = True
                # Tool execution error if applicable
                if (
                    hasattr(chat_message, "tool_call_id")
                    and chat_message.tool_call_id in tool_executions
                ):
                    tool_info = tool_executions.pop(chat_message.tool_call_id)
                yield (
                    create_sse_data({"type": "error", "content": "Unexpected error"}),
                    stream_started,
                )


async def process_message_chunk(msg: AIMessageChunk) -> str | None:
    """
    Process an AI message chunk and format it as an SSE message if needed.

    Args:
        msg: The AI message chunk to process

    Returns:
        str | None: Formatted SSE data string if content exists, None otherwise
    """
    content = remove_tool_calls(msg.content)
    if content:
        return create_sse_data(
            {
                "type": "stream_token",
                "content": {"token": convert_message_content_to_string(content)},
            }
        )
    return None


async def message_generator(
    user_input: UserInput,
    user_info: str,
    date: str,
    agent_id: str,
    agent_context: dict[str, Any],
) -> AsyncGenerator[str, None]:
    """
    Generate SSE messages from agent responses.

    Args:
        user_input: The user input to process
        agent_id: The ID of the agent to use
        agent_context: Additional context for the agent

    Yields:
        str: Formatted SSE data strings
    """
    agent: CompiledStateGraph = get_agent(agent_id)
    kwargs, run_id, thread_id = await _handle_input(user_input, agent, agent_context)
    tool_executions = {}
    completed_tools = []  # Track completed tools
    stream_started = False
    complete_message = ""
    try:
        # Simplified state creation without persistence
        state = CustomState(
            user_info=user_info,
            today_date=date,
            messages=kwargs["input"]["messages"],  # Only current message, no history
        )
        kwargs["input"] = state
        async for stream_event in agent.astream(
            **kwargs,
            stream_mode=["updates", "messages", "custom"],
        ):

            if not isinstance(stream_event, tuple):
                continue

            stream_mode, event = stream_event

            if stream_mode == "updates":
                async for message, new_stream_started in process_stream_updates(
                    event,
                    run_id,
                    thread_id,
                    user_input.message,
                    tool_executions,
                    stream_started,
                    completed_tools,
                ):
                    if (
                        "event: tool_execution_start" in message
                        or "event: tool_execution_complete" in message
                    ):
                        # Only yield tool-related events from updates mode
                        yield message
                    elif new_stream_started and not stream_started:
                        # Update stream_started if needed but don't yield duplicate stream_start
                        stream_started = new_stream_started

            elif stream_mode == "messages":
                msg, metadata = event
                if "skip_stream" in metadata.get("tags", []):
                    continue
                if not isinstance(msg, AIMessageChunk):
                    continue

                content = remove_tool_calls(msg.content)
                if content:
                    if not stream_started:
                        yield create_sse_data({"type": "stream_start", "content": None})
                        stream_started = True
                    complete_message += content
                    yield create_sse_data(
                        {
                            "type": "stream_token",
                            "content": {"token": convert_message_content_to_string(content)},
                        }
                    )

            elif stream_mode == "custom":
                if isinstance(event, Exception):
                    if not stream_started:
                        yield create_sse_data({"type": "stream_start", "content": None})
                        stream_started = True
                    yield create_sse_data({"type": "error", "content": str(event)})
                else:
                    yield create_sse_data(
                        {"type": event["event_type"].value, "content": event["data"]}
                    )

    except Exception as e:
        if not stream_started:
            yield create_sse_data({"type": "stream_start", "content": None})
        yield create_sse_data({"type": "error", "content": str(e)})
    finally:
        # Simplified cleanup - no active generation tracking needed
        
        if stream_started:
            # Only send stream_end if we actually started the stream
            yield create_sse_data({"type": "stream_end", "content": {"thread_id": thread_id}})


def _sse_response_example() -> dict[int, Any]:
    return {
        status.HTTP_200_OK: {
            "description": "Server-sent event response",
            "content": {
                "text/event-stream": {
                    "example": 'event: stream_start\n\nevent: stream_token\ndata: {"token": "Hello world"}\n\nevent: stream_end\ndata: {"thread_id": "abc123"}\n\n',
                    "schema": {"type": "string"},
                }
            },
        }
    }


@router.post(
    "/{agent_id}/stream",
    response_class=StreamingResponse,
    responses=_sse_response_example(),
)
async def stream(
    user_input: UserInput,
    agent_id: str,
) -> StreamingResponse:
    # Working without authentication - use default user info
    if not user_input.thread_id:
        user_input.thread_id = str(uuid4())

    # Get mock user info since we're working without authentication
    user_info = await get_user_info("mock_token", thread_id=user_input.thread_id, run_id=str(uuid4()))

    now_utc = datetime.now(timezone.utc)
    formatted_date = now_utc.strftime("%A, %B %d, %Y %I:%M %p")

    return StreamingResponse(
        message_generator(
            user_input,
            user_info,
            formatted_date,
            agent_id,
            {"bearer_token": "mock_token"},
        )
    )


app = create_app()


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Simple health check endpoint.

    Returns:
        dict: Status information about the service
    """
    return {
        "status": "ok",
        "version": API_VERSION,
        "message": "Application simple sans persistance - prêt pour les blagues et la météo ! 🎉"
    }


app.include_router(router)
