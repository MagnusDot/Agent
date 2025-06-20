#!/usr/bin/env python3
"""CLI interface for testing agents during development."""

import asyncio
import json
import os
import sys
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Prompt

# Add the project root to sys.path if not already there
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Load environment variables from .env file
dotenv_path = Path(__file__).parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded environment variables from {dotenv_path}")
else:
    # Try loading from the project root .env as a fallback
    root_dotenv = Path(__file__).parent.parent.parent / ".env"
    if root_dotenv.exists():
        load_dotenv(dotenv_path=root_dotenv)
        print(f"Loaded environment variables from {root_dotenv}")
    else:
        print("No .env file found. Using environment variables from the system.")

# Load config module
try:
    from utils.cli.config import AgentConfig, get_config
except ImportError:
    try:
        from cli.config import AgentConfig, get_config
    except ImportError:
        # If being run directly, import from the local directory
        sys.path.append(str(Path(__file__).parent))
        from config import AgentConfig, get_config

console = Console()


def display_agent_info(agent: AgentConfig) -> None:
    """Display information about an agent in a rich format."""
    console.print(
        Panel(f"[bold blue]{agent.name}[/bold blue]\n{agent.description}", title="Agent Info")
    )


def display_message(message: str, is_user: bool = False) -> None:
    """Display a message in the chat interface."""
    style = "bold green" if is_user else "bold blue"
    sender = "You" if is_user else "Agent"
    console.print(f"[{style}]{sender}:[/{style}] {message}")


async def stream_agent_response(
    client: httpx.AsyncClient,
    agent_id: str,
    message: str,
    conversation_id: str | None = None,
    debug: bool = False,
) -> str | None:
    """
    Stream the agent's response using the streaming API endpoint.

    Args:
        client: HTTP client
        agent_id: Agent ID
        message: User message
        conversation_id: Optional conversation ID to maintain context
        debug: Whether to show debug information

    Returns:
        The thread_id from the response if available, None otherwise
    """
    config = get_config()
    url = f"{config.api_url}/{agent_id}/stream"

    # Try different parameter names for conversation continuity
    payload = {"message": message}

    # Include bearer token in configurable context if available
    if config.bearer_token:
        if "context" not in payload:
            payload["context"] = {}
        payload["context"]["configurable"] = {"__bearer_token": config.bearer_token}
        if debug:
            console.print(
                f"[dim]Including bearer token in context (length: {len(config.bearer_token)})[/dim]"
            )

    if conversation_id:
        # Try all possible parameter names used by different API implementations
        payload["thread_id"] = conversation_id
        payload["conversation_id"] = conversation_id
        payload["chat_id"] = conversation_id

        # Only show conversation ID in debug mode
        if debug:
            console.print(f"[dim]Using conversation ID: {conversation_id}[/dim]")

    if debug:
        console.print("[dim]Sending request to API...[/dim]")
        console.print(f"[dim]URL: {url}[/dim]")
        console.print(f"[dim]Payload: {payload}[/dim]")

    try:
        async with client.stream("POST", url, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                error_msg = await response.aread()
                console.print(
                    f"[bold red]Error:[/bold red] Server returned status code {response.status_code}"
                )
                try:
                    error_data = json.loads(error_msg.decode("utf-8"))
                    console.print(
                        f"[bold red]Details:[/bold red] {error_data.get('detail', error_data)}"
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    console.print(
                        f"[bold red]Details:[/bold red] {error_msg.decode('utf-8', errors='replace')}"
                    )
                return None

            # Check possible header locations for conversation ID
            possible_header_ids = [
                response.headers.get("x-conversation-id"),
                response.headers.get("x-thread-id"),
                response.headers.get("x-chat-id"),
            ]
            header_id = next((id for id in possible_header_ids if id), None)
            if header_id and debug:
                console.print(f"[dim]Found conversation ID in header: {header_id}[/dim]")

            if debug:
                console.print("[dim]Connected to stream, waiting for response...[/dim]")

            # Process the SSE stream
            buffer = ""
            received_any_data = False
            agent_response = ""
            new_thread_id = None

            # Track thread_id locations for debugging
            thread_id_locations = []

            # Print agent response prefix
            console.print("[bold blue]Agent:[/bold blue] ", end="")

            async for chunk in response.aiter_text():
                received_any_data = True
                if debug:
                    console.print(f"[dim]Received chunk: {chunk!r}[/dim]", highlight=False)

                buffer += chunk
                lines = buffer.split("\n\n")
                buffer = lines.pop(-1)  # Keep the last incomplete chunk in the buffer

                for line in lines:
                    if debug:
                        console.print(f"[dim]Processing line: {line!r}[/dim]", highlight=False)

                    event_type = None
                    data_content = None

                    # Extract event type and data content
                    for subline in line.split("\n"):
                        if subline.startswith("event: "):
                            event_type = subline[7:].strip()
                            if debug:
                                console.print(f"[dim]Found event: {event_type}[/dim]")
                        elif subline.startswith("data: "):
                            try:
                                data_str = subline[6:]
                                data_content = json.loads(data_str)
                                if debug:
                                    console.print(f"[dim]Parsed data: {data_content!r}[/dim]")

                                # Check for any kind of ID in the data
                                if isinstance(data_content, dict):
                                    for id_key in ["thread_id", "conversation_id", "chat_id", "id"]:
                                        if id_key in data_content:
                                            new_thread_id = data_content[id_key]
                                            thread_id_locations.append(
                                                f"{id_key} in {event_type or 'data'}"
                                            )
                                            if debug:
                                                console.print(
                                                    f"[dim]Found {id_key}: {new_thread_id}[/dim]"
                                                )
                            except json.JSONDecodeError as e:
                                if debug:
                                    console.print(
                                        f"[bold red]JSON Error:[/bold red] {str(e)} - in data: {subline[6:]!r}"
                                    )

                    # If no explicit event type, try to infer from data structure
                    if not event_type and data_content:
                        if isinstance(data_content, dict):
                            # Check for token format - we know it's stream_token
                            if "token" in data_content:
                                event_type = "stream_token"
                            # Check for tool-like structure in the data
                            elif "name" in data_content and (
                                "input" in data_content or "output" in data_content
                            ):
                                if "input" in data_content and "output" not in data_content:
                                    event_type = "tool_execution_start"
                                elif "output" in data_content:
                                    event_type = "tool_end"
                                elif "error" in data_content:
                                    event_type = "tool_error"

                    if not event_type or data_content is None:
                        if "data: " in line and not line.startswith("event:"):
                            # Handle case where only data is provided without event
                            try:
                                data_line = next(
                                    (
                                        line_item
                                        for line_item in line.split("\n")
                                        if line_item.startswith("data: ")
                                    ),
                                    "",
                                )
                                if data_line:
                                    data_str = data_line[6:]  # Remove "data: " prefix
                                    token = json.loads(data_str)
                                    if isinstance(token, str):
                                        console.print(token, end="", soft_wrap=True)
                                        agent_response += token
                                    elif isinstance(token, dict):
                                        # Check for thread_id in the data
                                        if "thread_id" in token:
                                            new_thread_id = token["thread_id"]
                                            if debug:
                                                console.print(
                                                    f"[dim]Found thread_id: {new_thread_id}[/dim]"
                                                )

                                        # Handle token field (new format) - we know it's stream_token
                                        if "token" in token:
                                            token_text = token["token"]
                                            console.print(token_text, end="", soft_wrap=True)
                                            agent_response += token_text
                                        # Handle content field (legacy format)
                                        elif "content" in token:
                                            content = token["content"]
                                            console.print(content, end="", soft_wrap=True)
                                            agent_response += content
                            except json.JSONDecodeError:
                                pass
                        continue

                    # Handle different event types
                    if event_type == "stream_token":  # We know the event type is stream_token
                        if isinstance(data_content, str):
                            # Handle legacy format where token is a string
                            console.print(data_content, end="", soft_wrap=True)
                            agent_response += data_content
                        elif isinstance(data_content, dict):
                            # Check for thread_id in the token data
                            if "thread_id" in data_content:
                                new_thread_id = data_content["thread_id"]
                                if debug:
                                    console.print(
                                        f"[dim]Found thread_id in token: {new_thread_id}[/dim]"
                                    )

                            # Handle the new format where token is a field in the dict
                            if "token" in data_content:
                                token_text = data_content["token"]
                                console.print(token_text, end="", soft_wrap=True)
                                agent_response += token_text
                            # Handle legacy format where content is a field in the dict
                            elif "content" in data_content:
                                content = data_content["content"]
                                console.print(content, end="", soft_wrap=True)
                                agent_response += content

                    elif event_type in ["tool_execution_start"]:
                        # When a tool starts being used
                        tool_name = data_content.get("name", "Unknown tool")
                        # Support both input and params field
                        tool_input = data_content.get("input", data_content.get("params", {}))
                        console.print(
                            f"\n[bold yellow]Using tool:[/bold yellow] [bold cyan]{tool_name}[/bold cyan]"
                        )
                        console.print(f"[dim]Tool input: {json.dumps(tool_input, indent=2)}[/dim]")

                    elif event_type in ["tool_end", "tool_execution_complete"]:
                        # When a tool finishes execution
                        tool_name = data_content.get("name", "Unknown tool")
                        console.print(
                            f"[bold yellow]Tool complete:[/bold yellow] [bold cyan]{tool_name}[/bold cyan]"
                        )
                        # Display tool output in a more compact form if available
                        if "output" in data_content:
                            tool_output = data_content.get("output")
                            if isinstance(tool_output, str) and len(tool_output) > 100:
                                console.print(
                                    f"[dim]Tool output: {tool_output[:100]}...(truncated)[/dim]"
                                )
                            else:
                                console.print(f"[dim]Tool output: {tool_output}[/dim]")

                        # Start a new line for continuing the agent's response
                        console.print("\n[bold blue]Agent:[/bold blue] ", end="")

                    elif event_type in ["tool_error", "tool_execution_error"]:
                        # When a tool encounters an error
                        tool_name = data_content.get("name", "Unknown tool")
                        error_message = data_content.get("error", "Unknown error")
                        console.print(
                            f"\n[bold red]Tool Error:[/bold red] [bold cyan]{tool_name}[/bold cyan]"
                        )
                        console.print(f"[bold red]Error message:[/bold red] {error_message}")

                        # Start a new line for continuing the agent's response
                        console.print("\n[bold blue]Agent:[/bold blue] ", end="")

                    elif event_type == "stream_end":
                        # When the stream ends, check for thread_id in the content
                        if isinstance(data_content, dict) and "thread_id" in data_content:
                            new_thread_id = data_content["thread_id"]
                            thread_id_locations.append("thread_id in stream_end")
                            if debug:
                                console.print(
                                    f"\n[dim]Found thread_id in stream_end: {new_thread_id}[/dim]"
                                )

                    elif debug:
                        # Log other event types in debug mode
                        console.print(f"\n[dim]Event: {event_type}[/dim]")
                        console.print(f"[dim]Data: {data_content}[/dim]")

            if not received_any_data:
                console.print(
                    "[bold yellow]Warning:[/bold yellow] No data received from the server"
                )
            elif not agent_response:
                console.print(
                    "[bold yellow]Warning:[/bold yellow] No displayable content found in the response"
                )
                if debug:
                    console.print(
                        "[bold yellow]Try running with --debug to see the raw response format[/bold yellow]"
                    )

    except httpx.HTTPError as e:
        console.print(f"[bold red]HTTP Error:[/bold red] {str(e)}")
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Received invalid JSON from server")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

    console.print()  # Add a newline after the streaming is complete

    # For stream endpoint, only return thread_id from stream_end event
    return new_thread_id


async def invoke_agent_response(
    client: httpx.AsyncClient,
    agent_id: str,
    message: str,
    conversation_id: str | None = None,
    debug: bool = False,
) -> str | None:
    """
    Get the complete response from the agent using the invoke API endpoint.

    Args:
        client: HTTP client
        agent_id: Agent ID
        message: User message
        conversation_id: Optional conversation ID to maintain context
        debug: Whether to show debug information

    Returns:
        The thread_id from the response if available, None otherwise
    """
    config = get_config()
    url = f"{config.api_url}/{agent_id}/invoke"

    # Try different parameter names for conversation continuity
    payload = {"message": message}

    # Include bearer token in configurable context if available
    if config.bearer_token:
        if "context" not in payload:
            payload["context"] = {}
        payload["context"]["configurable"] = {"__bearer_token": config.bearer_token}
        if debug:
            console.print(
                f"[dim]Including bearer token in context (length: {len(config.bearer_token)})[/dim]"
            )

    if conversation_id:
        # Try all possible parameter names used by different API implementations
        payload["thread_id"] = conversation_id
        payload["conversation_id"] = conversation_id
        payload["chat_id"] = conversation_id

        # Only show conversation ID in debug mode
        if debug:
            console.print(f"[dim]Using conversation ID: {conversation_id}[/dim]")

    if debug:
        console.print("[dim]Sending request to API...[/dim]")
        console.print(f"[dim]URL: {url}[/dim]")
        console.print(f"[dim]Payload: {payload}[/dim]")

    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]Waiting for response...", total=1)

            response = await client.post(url, json=payload, timeout=60.0)
            progress.update(task, completed=1)

            # Check possible header locations for conversation ID
            possible_header_ids = [
                response.headers.get("x-conversation-id"),
                response.headers.get("x-thread-id"),
                response.headers.get("x-chat-id"),
            ]
            header_id = next((id for id in possible_header_ids if id), None)
            if header_id and debug:
                console.print(f"[dim]Found conversation ID in header: {header_id}[/dim]")

            if response.status_code != 200:
                console.print(
                    f"[bold red]Error:[/bold red] Server returned status code {response.status_code}"
                )
                try:
                    error_data = response.json()
                    console.print(
                        f"[bold red]Details:[/bold red] {error_data.get('detail', error_data)}"
                    )
                except json.JSONDecodeError:
                    console.print(f"[bold red]Details:[/bold red] {response.text}")
                return None

            if debug:
                console.print(f"[dim]Response headers: {dict(response.headers)}[/dim]")

            try:
                data = response.json()
                if debug:
                    console.print(f"[dim]Response data: {data}[/dim]")

                # Extract thread_id from response - only look for explicit thread_id
                new_thread_id = None
                if isinstance(data, dict) and "thread_id" in data:
                    new_thread_id = data["thread_id"]
                    if debug:
                        console.print(f"[dim]Found thread_id in response: {new_thread_id}[/dim]")

                # Handle different response formats
                if "output" in data:
                    console.print(Markdown(data["output"]))
                elif "response" in data:
                    console.print(Markdown(data["response"]))
                elif "content" in data:
                    console.print(Markdown(data["content"]))
                elif "text" in data:
                    console.print(Markdown(data["text"]))
                elif "message" in data:
                    console.print(Markdown(data["message"]))
                elif isinstance(data, str):
                    console.print(Markdown(data))
                else:
                    console.print(
                        "[bold yellow]Warning:[/bold yellow] No recognized output field in response"
                    )
                    if debug:
                        console.print(
                            f"[dim]Available fields: {list(data.keys() if isinstance(data, dict) else [])}[/dim]"
                        )

                # For invoke endpoint, only return thread_id from response body
                return new_thread_id
            except json.JSONDecodeError as e:
                console.print(f"[bold red]JSON Error:[/bold red] {str(e)}")
                if debug:
                    console.print(f"[dim]Raw response: {response.text!r}[/dim]")

    except httpx.HTTPError as e:
        console.print(f"[bold red]HTTP Error:[/bold red] {str(e)}")
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Received invalid JSON from server")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

    return None


async def ensure_api_is_running(client: httpx.AsyncClient) -> bool:
    """Check if the API is running by pinging the health endpoint."""
    config = get_config()
    url = f"{config.api_url}/health"

    try:
        response = await client.get(url, timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


async def get_available_agents(client: httpx.AsyncClient) -> list[AgentConfig]:
    """Get available agents from the API or fallback to config if API not available."""
    config = get_config()

    try:
        response = await client.get(f"{config.api_url}/agents", timeout=5.0)
        if response.status_code == 200:
            agents_data = response.json()
            return [
                AgentConfig(
                    id=agent["key"], name=agent["key"], description=agent.get("description", "")
                )
                for agent in agents_data
            ]
    except Exception:
        pass

    # Fallback to config
    return config.agents


@click.group()
def cli():
    """CLI interface for testing agents during development."""
    pass


@cli.command()
@click.option("--api-url", help="Override the API URL from config")
@click.option("--bearer-token", help="Bearer token for API authentication")
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode with verbose output")
def check(api_url: str | None, bearer_token: str | None, debug: bool):
    """Check API connectivity."""
    if api_url:
        os.environ["API_URL"] = api_url
    if bearer_token:
        os.environ["BEARER_TOKEN"] = bearer_token

    async def run_check():
        config = get_config()
        console.print(f"Checking API at {config.api_url}...")

        # Create headers dict with bearer token if available
        headers = {}
        if config.bearer_token:
            headers["Authorization"] = f"Bearer {config.bearer_token}"
            if debug:
                console.print("[dim]Using bearer token for authentication[/dim]")

        async with httpx.AsyncClient(headers=headers) as client:
            # Check health endpoint
            try:
                health_url = f"{config.api_url}/health"
                health_response = await client.get(health_url, timeout=5.0)
                if health_response.status_code == 200:
                    console.print("[green]✓[/green] Health endpoint is available")
                else:
                    console.print(
                        f"[yellow]✗[/yellow] Health endpoint returned status {health_response.status_code}"
                    )
            except Exception as e:
                console.print(f"[red]✗[/red] Health endpoint error: {str(e)}")

            # Check agents endpoint
            try:
                agents_url = f"{config.api_url}/agents"
                agents_response = await client.get(agents_url, timeout=5.0)
                if agents_response.status_code == 200:
                    agents = agents_response.json()
                    console.print(f"[green]✓[/green] Found {len(agents)} agents")
                    for agent in agents:
                        console.print(
                            f"  [blue]•[/blue] {agent.get('key', 'Unknown')}: {agent.get('description', 'No description')}"
                        )
                else:
                    console.print(
                        f"[yellow]✗[/yellow] Agents endpoint returned status {agents_response.status_code}"
                    )
            except Exception as e:
                console.print(f"[red]✗[/red] Agents endpoint error: {str(e)}")

    asyncio.run(run_check())


@cli.command()
@click.option("--agent", "-a", help="The agent ID to test")
@click.option("--invoke", "-i", is_flag=True, help="Use invoke instead of streaming")
@click.option("--api-url", help="Override the API URL from config")
@click.option("--bearer-token", help="Bearer token for API authentication")
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode with verbose output")
@click.option("--no-context", is_flag=True, help="Disable conversation context tracking")
def chat(
    agent: str | None,
    invoke: bool,
    api_url: str | None,
    bearer_token: str | None,
    debug: bool,
    no_context: bool,
):
    """Start an interactive chat session with an agent."""
    if api_url:
        os.environ["API_URL"] = api_url
    if bearer_token:
        os.environ["BEARER_TOKEN"] = bearer_token

    async def run_chat():
        nonlocal debug  # Add this line to access the outer debug variable
        config = get_config()

        # Create headers dict with bearer token if available
        headers = {}
        if config.bearer_token:
            headers["Authorization"] = f"Bearer {config.bearer_token}"
            if debug:
                console.print("[dim]Using bearer token for authentication[/dim]")

        async with httpx.AsyncClient(headers=headers) as client:
            # Check if API is running
            with console.status("[bold yellow]Checking if API is running..."):
                api_running = await ensure_api_is_running(client)

            if not api_running:
                console.print("[bold red]Error:[/bold red] Could not connect to the API.")
                console.print(f"Make sure the API is running at {config.api_url}")
                return

            # Get available agents
            with console.status("[bold yellow]Fetching available agents..."):
                agents = await get_available_agents(client)

            if not agents:
                console.print("[bold red]Error:[/bold red] No agents available.")
                return

            # Select agent if not provided
            agent_id = agent
            if not agent_id:
                console.print("\n[bold]Available Agents:[/bold]")
                for i, agent_config in enumerate(agents, 1):
                    console.print(
                        f"[bold cyan]{i}[/bold cyan]. {agent_config.name} - {agent_config.description}"
                    )

                # Use numeric selection
                try:
                    agent_index = (
                        int(
                            Prompt.ask(
                                "\nSelect an agent by number",
                                choices=[str(i) for i in range(1, len(agents) + 1)],
                            )
                        )
                        - 1
                    )
                    agent_id = agents[agent_index].id
                except (ValueError, IndexError):
                    console.print("[bold red]Error:[/bold red] Invalid selection.")
                    return

            # Validate agent exists
            agent_exists = any(a.id == agent_id for a in agents)
            if not agent_exists:
                console.print(f"[bold red]Error:[/bold red] Agent '{agent_id}' not found.")
                return

            # Selected agent info
            selected_agent = next(a for a in agents if a.id == agent_id)

            console.print(
                f"\n[bold green]Starting chat session with[/bold green] [bold blue]{selected_agent.name}[/bold blue]"
            )
            if no_context:
                console.print(
                    "[bold yellow]Context tracking disabled[/bold yellow] - each message will be treated as a new conversation"
                )
            else:
                console.print(
                    "[bold green]Context tracking enabled[/bold green] - conversation history will be preserved"
                )

            # Display available special commands
            console.print("\n[bold]Available Commands:[/bold]")
            console.print("  [yellow]!clear[/yellow] - Clear conversation context/history")
            console.print("  [yellow]!debug[/yellow] - Toggle debug mode")
            console.print("  [yellow]exit[/yellow]   - End the chat session")

            console.print("\nType 'exit' to end the session\n")

            # Conversation ID (will be updated with server responses)
            conversation_id = None

            # Chat loop
            while True:
                # Get user input but do not display yet as the Prompt already displays the prompt with "You:"
                message_input = Prompt.ask("\n[bold green]You[/bold green]")
                if message_input.lower() == "exit":
                    break

                # Special commands
                if message_input.lower() == "!clear":
                    console.print("[bold yellow]Clearing conversation context...[/bold yellow]")
                    conversation_id = None
                    continue
                elif message_input.lower() == "!debug":
                    debug = not debug
                    console.print(
                        f"[bold yellow]Debug mode {'enabled' if debug else 'disabled'}[/bold yellow]"
                    )
                    continue

                # Report conversation ID status only in debug mode
                if conversation_id and not no_context and debug:
                    console.print(f"[dim]Chat is in-context with ID: {conversation_id}[/dim]")

                # Make the API request with payload including thread_id
                if no_context:
                    # If no_context is true, we don't want to use or update the conversation_id
                    if invoke:
                        await invoke_agent_response(client, agent_id, message_input, None, debug)
                    else:
                        await stream_agent_response(client, agent_id, message_input, None, debug)
                else:
                    # Use and update the conversation_id
                    if invoke:
                        new_id = await invoke_agent_response(
                            client, agent_id, message_input, conversation_id, debug
                        )
                        if new_id:
                            conversation_id = new_id
                            if debug:
                                console.print(
                                    f"[dim]Updated conversation ID from invoke response: {conversation_id}[/dim]"
                                )
                    else:
                        new_id = await stream_agent_response(
                            client, agent_id, message_input, conversation_id, debug
                        )
                        if new_id:
                            conversation_id = new_id
                            if debug:
                                console.print(
                                    f"[dim]Updated conversation ID from stream response: {conversation_id}[/dim]"
                                )

    asyncio.run(run_chat())


if __name__ == "__main__":
    cli()
