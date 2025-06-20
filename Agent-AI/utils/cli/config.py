"""Configuration file for the agent testing CLI."""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    id: str
    name: str
    description: str


class Config(BaseModel):
    """Configuration for the agent testing CLI."""

    api_url: str = Field(default="http://localhost:8080", description="The base URL of the API.")
    agents: list[AgentConfig] = Field(default_factory=list, description="List of available agents.")
    bearer_token: str | None = Field(
        default=None, description="Optional bearer token for API authentication."
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        api_url = os.environ.get("API_URL", "http://localhost:8080")
        bearer_token = os.environ.get("BEARER_TOKEN")

        return cls(api_url=api_url, agents=[], bearer_token=bearer_token)

    @classmethod
    def from_json(cls, file_path: str) -> "Config":
        """Load configuration from a JSON file."""
        try:
            with open(file_path) as f:
                data = json.load(f)
            return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            print(f"Error loading config from {file_path}: {str(e)}")
            return default_config


# Default configuration
default_config = Config(
    api_url="http://localhost:8080",
    agents=[
        AgentConfig(
            id="sallyC",
            name="SallyC",
            description="An AI agent that can help users explore opportunities in the Reply CRM.",
        ),
        # Add more agents as needed
    ],
)


def get_config() -> Config:
    """
    Get the configuration from (in order of precedence):
    1. Environment variables
    2. JSON config file (utils/cli/agents_config.json)
    3. Default hardcoded config

    Note: BEARER_TOKEN is always checked in environment variables first,
    regardless of where the rest of the config comes from.
    """
    config = None

    # Check for API_URL in environment variables
    if os.environ.get("API_URL"):
        config = Config.from_env()
    else:
        # Check for JSON config file
        config_file = Path(__file__).parent / "agents_config.json"
        if config_file.exists():
            config = Config.from_json(str(config_file))
        else:
            # Fallback to default config
            config = default_config

    # Always override bearer_token from environment if available
    if os.environ.get("BEARER_TOKEN") and not config.bearer_token:
        bearer_token = os.environ.get("BEARER_TOKEN")
        config.bearer_token = bearer_token

    return config
