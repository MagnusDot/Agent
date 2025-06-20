# Makefile for common operations

# Environment variables
PYTHON := python
UVICORN := uvicorn
PORT := 8080
HOST := 0.0.0.0
API_URL ?= http://localhost:8080
DEBUG ?= 0

# Default agent (can be overridden via AGENT=agent_name)
AGENT ?=

# Help target
.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Server commands:"
	@echo "  make run-server         Run the API server"
	@echo "  make run-server-dev     Run the API server in development mode"
	@echo ""
	@echo "CLI commands:"
	@echo "  make cli                Run the agent CLI"
	@echo "  make cli-stream         Run the agent CLI with streaming enabled (default)"
	@echo "  make cli-invoke         Run the agent CLI with invoke mode (no streaming)"
	@echo "  make cli-debug          Run the agent CLI with debug mode"
	@echo "  make cli-agent          Run CLI with a specific agent (make cli-agent AGENT=agent_name)"
	@echo "  make check              Check API status and available agents"
	@echo ""
	@echo "Development setup:"
	@echo "  make setup              Setup development environment"
	@echo "  make env-init           Create initial .env file from template"
	@echo "  make env-edit           Open .env file in your default editor"
	@echo ""
	@echo "Testing commands:"
	@echo "  make test               Run all tests"
	@echo "  make test-cov           Run tests with coverage report"
	@echo "  make test-unit          Run unit tests"
	@echo "  make test-integration   Run integration tests"
	@echo "  make test-tools         Run tools tests"
	@echo ""
	@echo "Code quality:"
	@echo "  make lint               Run linting tools"
	@echo "  make format             Auto-format code"
	@echo "  make clean              Clean up temporary files"
	@echo ""
	@echo "Docker commands:"
	@echo "  make docker-build       Build Docker container"
	@echo "  make docker-run         Run with Docker Compose"
	@echo "  make docker-prod        Run with production Docker Compose"
	@echo "  make docker-stop        Stop Docker containers"

# Development setup
.PHONY: setup env-init env-edit
setup:
	test -f .env || cp .env.example .env
	pip install -e ".[dev]"

env-init:
	test -f .env || cp .env.example .env
	@echo ".env file created from template"

env-edit:
	${EDITOR} .env || (echo "No editor set. Set the EDITOR environment variable." && false)

# Server
.PHONY: run-server run-server-dev
run-server:
	cd Agent-AI && $(PYTHON) src/main.py

dev:
	@echo "Environment variables from .env file:"
	@grep -v "^#" .env 2>/dev/null || echo "No .env file found in root directory"
	@echo "\nStarting application..."
	cd Agent-AI && ([ -f ../.env ] && set -a && source ../.env && set +a && LOG_FILES=TRUE $(PYTHON) src/main.py || LOG_FILES=TRUE $(PYTHON) src/main.py)

# CLI operations
.PHONY: cli cli-stream cli-invoke cli-debug cli-agent check
cli: cli-stream

cli-stream:
	cd Agent-AI && $(PYTHON) utils/cli/agent_cli.py chat

cli-invoke:
	cd Agent-AI && $(PYTHON) utils/cli/agent_cli.py chat --invoke

cli-debug:
	cd Agent-AI && $(PYTHON) utils/cli/agent_cli.py chat --debug

cli-agent:
ifdef AGENT
	cd Agent-AI && $(PYTHON) utils/cli/agent_cli.py chat --agent $(AGENT) $(if $(filter 1,$(DEBUG)),--debug)
else
	@echo "Please specify an agent using AGENT=agent_name"
	@echo "Example: make cli-agent AGENT=math_agent"
	@echo "Add DEBUG=1 to enable debug mode: make cli-agent AGENT=math_agent DEBUG=1"
endif

# Run CLI with custom API URL
.PHONY: cli-api
cli-api:
	cd Agent-AI && $(PYTHON) utils/cli/agent_cli.py chat --api-url $(API_URL) $(if $(filter 1,$(DEBUG)),--debug)

check:
	cd Agent-AI && $(PYTHON) utils/cli/agent_cli.py check --api-url $(API_URL)
