"""Tests for the dotenv loading in the agent CLI."""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

from dotenv import load_dotenv


def test_dotenv_loading():
    """Test that the .env file is properly loaded."""
    mock_env_content = "API_URL=http://test-api-url\nBEARER_TOKEN=test-dotenv-token"

    # Use mock_open to simulate a .env file
    with (
        patch("builtins.open", mock_open(read_data=mock_env_content)),
        patch("os.path.exists", return_value=True),
        patch.dict(os.environ, {}, clear=True),
        patch("dotenv.find_dotenv", return_value=".env"),
    ):
        # Load the dotenv file
        load_dotenv()

        # Check if environment variables were set correctly
        assert os.environ.get("API_URL") == "http://test-api-url"
        assert os.environ.get("BEARER_TOKEN") == "test-dotenv-token"


def test_cli_imports_dotenv():
    """Test that the agent_cli script imports dotenv."""
    agent_cli_path = Path(__file__).parent.parent / "agent_cli.py"
    assert agent_cli_path.exists(), "agent_cli.py not found"

    with open(agent_cli_path) as file:
        content = file.read()
        assert "from dotenv import load_dotenv" in content, "Dotenv import not found"
        assert "load_dotenv" in content, "load_dotenv function call not found"
