# Agent Testing CLI

A command-line interface for testing agents during development via the API interface.

## Installation

The CLI uses the following development dependencies:
- click
- rich
- httpx

These are automatically included in your development dependencies when you install the project.

## Usage

### Basic usage

Start the CLI to test agents with streaming responses:

```bash
# Run as a module (recommended)
python -m utils.cli.agent_cli chat

# Or run directly as a script
python utils/cli/agent_cli.py chat
```

### Command-line options

#### Chat command

- `--agent`, `-a`: Specify the agent ID to test directly
- `--invoke`, `-i`: Use invoke endpoint instead of streaming
- `--api-url`: Override the API URL (default: http://localhost:8080)
- `--bearer-token`: Specify a bearer token for API authentication
- `--debug`, `-d`: Enable debug mode with verbose output
- `--no-context`: Disable conversation context tracking

Example:

```bash
python -m utils.cli.agent_cli chat --agent sallyC --invoke
```

For authenticated API access:

```bash
python -m utils.cli.agent_cli chat --bearer-token "your-token-here"
```

For troubleshooting, use debug mode:

```bash
python -m utils.cli.agent_cli chat --debug
```

To test without conversation memory:

```bash
python -m utils.cli.agent_cli chat --no-context
```

### Special commands

During a chat session, you can use these special commands:

- `!clear` - Clear the conversation context (reset memory)
- `!debug` - Toggle debug mode on/off
- `exit` - End the chat session

#### Check command

Check the API connectivity and available agents:

```bash
python -m utils.cli.agent_cli check
```

You can also override the API URL and provide authentication:

```bash
python -m utils.cli.agent_cli check --api-url "http://localhost:8080" --bearer-token "your-token-here"
```

## Conversation Context

The CLI maintains conversation context between messages using a client-side generated ID. Here's how it works:

1. When starting a new chat, the CLI generates a unique conversation ID (`cli-{uuid}`)
2. This ID is sent with each message to the API
3. The API uses this ID to link messages in the same conversation

This approach ensures conversation continuity without requiring the server to return a thread ID. Benefits include:

- Works with any API implementation
- Consistent conversation tracking
- No dependency on server-side thread management
- Easy to debug and reset the conversation

**Special commands for conversation management:**
- `!clear` - Generates a new conversation ID (resets the conversation)

The CLI tries multiple parameter names for compatibility with different API implementations:

**Parameter names used:**
- `thread_id`
- `conversation_id`
- `chat_id`

## API Endpoints Used

The CLI assumes the following API endpoints:

- `GET /health` - Health check endpoint
- `GET /agents` - List all available agents
- `POST /{agent_id}/stream` - Stream response from an agent
- `POST /{agent_id}/invoke` - Get complete response from an agent

The payload format for both stream and invoke endpoints is:

```json
{
  "message": "Your message to the agent",
  "thread_id": "optional-thread-id-for-context"
}
```

The server returns a conversation ID (thread_id, conversation_id, etc.) in the response data, which the CLI uses for subsequent requests to maintain conversation context.

### Streaming Response Format

The streaming endpoint is expected to return Server-Sent Events (SSE) with the following format:

```
event: stream_token
data: {"token": "token content"}

```

### Tool Usage Display

The CLI supports displaying tool usage in the chat interface. It recognizes the following event types:

- `event: tool_execution_start` - When an agent starts using a tool
- `event: tool_execution_complete` - When a tool execution completes
- `event: tool_execution_error` - When a tool encounters an error

Example of tool usage events:

```
event: tool_execution_start
data: {"name": "get_opportunities", "params": {"query": "recent opportunities"}}

event: tool_execution_complete
data: {"name": "get_opportunities", "params": {"query": "recent opportunities"}}
```

Alternative format (legacy, also supported):

```
event: tool_start
data: {"name": "search", "input": {"query": "weather in New York"}}

event: tool_end
data: {"name": "search", "output": "The weather in New York is sunny, 75°F."}

event: tool_error
data: {"name": "search", "error": "Failed to connect to search service."}
```

When these events are detected, the CLI will display them with appropriate formatting:
- Tool usage is highlighted in yellow and cyan
- Tool inputs and outputs are displayed in a readable format
- The chat flow is maintained with proper spacing

## Configuration

You can configure the available agents and API URL in several ways:

### 1. Using a .env file

Create or modify the `.env` file in the `utils/cli` directory:

```
# API URL (default: http://localhost:8080)
API_URL=http://localhost:8080

# Bearer token for authentication (optional)
BEARER_TOKEN=your-auth-token-here
```

A `.env.example` file is provided as a template.

### 2. Using a JSON config file

Create or edit the `utils/cli/agents_config.json` file:

```json
{
  "api_url": "http://localhost:8080",
  "bearer_token": "optional-auth-token",
  "agents": [
    {
      "id": "sallyC",
      "name": "SallyO",
      "description": "An AI agent that can help users explore opportunities in the Reply CRM."
    },
    {
      "id": "custom_agent",
      "name": "Custom Agent",
      "description": "Your custom agent description."
    }
  ]
}
```

### 2. Using environment variables

Set the `API_URL` and optionally `BEARER_TOKEN` environment variables:

```bash
export API_URL="http://localhost:8080"
export BEARER_TOKEN="your-auth-token"
python -m utils.cli.agent_cli chat
```

### 3. Using command-line options

```bash
python -m utils.cli.agent_cli chat --api-url "http://localhost:8080" --bearer-token "your-auth-token"
```

## Development Notes

- The CLI is designed as a development tool only
- It automatically fetches available agents from the API if running
- It falls back to the configured agents list if the API is not available
- You can exit the chat session by typing "exit"
- Use the `check` command to diagnose API connectivity issues
- Enable debug mode with `--debug` to see detailed API requests and responses
- Tool usage is displayed inline with different formatting to distinguish it from regular output
- Conversation context can be disabled with `--no-context` or cleared during chat with `!clear`
