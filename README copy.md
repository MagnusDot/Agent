# GenAI Agent Backend Template

A FastAPI backend template for building GenAI agent applications. This template provides a complete setup for creating, managing, and deploying GenAI agents with a scalable architecture.

## Features

- FastAPI web server with comprehensive API for agent interaction
- LangGraph integration for agent workflow management
- Built-in agent memory with database persistence
- Streaming response support via Server-Sent Events (SSE)
- Environment-based configuration
- Docker support for containerized deployment
- Testing setup with pytest
- Code quality tools with pre-commit and ruff
- Comprehensive Makefile for development workflows

## Prerequisites

- Python 3.11 or higher (tested up to 3.13)
- Docker (optional, for containerization)

## Getting Started

### Environment Setup

1. Clone the repository
2. Create a virtual environment and install dependencies:
   ```sh
   pipx install uv
   uv sync --frozen
   source .venv/bin/activate
   ```

   Or use Make to set up the environment:
   ```sh
   make setup
   ```

3. Create an environment file:
   ```sh
   cp .env.example .env
   ```

   Or use Make:
   ```sh
   make env-init
   ```

### Running Locally

Start the application:

```sh
python src/main.py
```

Or use Make:

```sh
make run-server      # Standard mode
make dev             # Development mode with environment loading
```

The application will be available at http://localhost:8080.

### API Endpoints

- `GET /health` - Health check endpoint that returns status information about the application and database
- `GET /agents` - Lists all available agents with their descriptions
- `POST /{agent_id}/invoke` - Synchronous agent invocation endpoint
- `POST /{agent_id}/stream` - Streaming agent invocation endpoint using Server-Sent Events (SSE)

## Project Structure

- `src/`: Main application code
  - `agents/`: Agent definitions and implementations
  - `app/`: FastAPI application and routing
  - `core/`: Core functionality and settings
  - `memory/`: Agent memory and database persistence
  - `schema/`: Data models and schemas
  - `tools/`: Tool implementations for agents
- `tests/`: Test suite
- `utils/`: Utility functions and helpers

## Adding New Agents

To add a new agent:

1. Create a new agent implementation in the `src/agents/` directory
2. Register the agent in `src/agents/agents.py`
3. Implement any required tools in the `src/tools/` directory

## Configuration

Configuration is managed through environment variables, which can be set in the `.env` file:

- `HOST`: The host to bind the server to (default: `0.0.0.0`)
- `PORT`: The port to bind the server to (default: `8080`)
- `MODE`: Application mode, set to `dev` for development features like auto-reload
- `DATABASE_URL`: URL for the database connection (default: SQLite file)

To edit your environment configuration:

```sh
make env-edit
```

## Make Commands

This project includes a comprehensive Makefile to simplify development workflows:

### Server Commands
- `make run-server` - Run the API server
- `make dev` - Run the API server in development mode with environment loading

### CLI Commands
- `make cli` - Run the agent CLI with streaming (default)
- `make cli-invoke` - Run the agent CLI without streaming
- `make cli-debug` - Run the agent CLI with debug mode
- `make cli-agent AGENT=agent_name` - Run CLI with a specific agent
- `make check` - Check API status and available agents

### Development Setup
- `make setup` - Setup development environment
- `make env-init` - Create initial .env file from template
- `make env-edit` - Open .env file in your default editor

### Testing Commands
- `make test` - Run all tests
- `make test-cov` - Run tests with coverage report
- `make test-unit` - Run unit tests
- `make test-integration` - Run integration tests
- `make test-tools` - Run tools tests

### Code Quality
- `make lint` - Run linting tools
- `make format` - Auto-format code
- `make clean` - Clean up temporary files
- `make install-hooks` - Install pre-commit hooks

### Docker Commands
- `make docker-build` - Build Docker container
- `make docker-run` - Run with Docker Compose
- `make docker-prod` - Run with production Docker Compose
- `make docker-stop` - Stop Docker containers

## Docker

### Building the Docker Image

```sh
docker build -t genai-agent-be .
```

Or use Make:

```sh
make docker-build
```

### Running with Docker Compose

```sh
docker compose up
```

Or use Make:

```sh
make docker-run       # Development configuration
make docker-prod      # Production configuration
```

## Testing and Development Utilities

This project includes several utilities to help with testing and development of agents:

### CLI Testing Tool

A command-line interface tool is provided for interactive testing of agents during development:

```sh
# Run as a module (recommended)
python -m utils.cli.agent_cli chat

# Or run directly as a script
python utils/cli/agent_cli.py chat

# Using Make
make cli
```

#### CLI Features:

- Interactive chat with any agent in the system
- Support for both streaming and non-streaming responses
- Conversation context tracking across messages
- Debug mode for viewing detailed request/response data
- Special commands like `!clear` (reset conversation) and `!debug` (toggle debug mode)

#### CLI Usage Examples:

```sh
# Start interactive chat with agent selection
python -m utils.cli.agent_cli chat
# Or: make cli

# Test a specific agent with streaming responses
python -m utils.cli.agent_cli chat --agent sallyC
# Or: make cli-agent AGENT=sallyC

# Use non-streaming invoke endpoint instead
python -m utils.cli.agent_cli chat --invoke
# Or: make cli-invoke

# Check API connectivity and available agents
python -m utils.cli.agent_cli check
# Or: make check
```

For more details, see the CLI documentation in `utils/cli/README.md`.

### Bruno API Collections

[Bruno](https://www.usebruno.com/) API collections are included for testing API endpoints directly:

Located in the `utils/bruno/` directory, these collections provide:

- Ready-to-use requests for all API endpoints
- Environment configuration for different setups
- Examples for both streaming and non-streaming requests

To use these collections:
1. Install the Bruno app from [usebruno.com](https://www.usebruno.com/)
2. Open the collection from the `utils/bruno/` directory
3. Configure the environment variables if needed
4. Run the requests to test your API endpoints

Available Bruno files:
- `health_check.bru` - Test API health endpoint

## Development Tools

- **pre-commit**: Runs code quality checks before commits
- **ruff**: Python linter and formatter
- **pytest**: Testing framework

To install pre-commit hooks:

```sh
make install-hooks
```
