"""Tests for the config module in the agent CLI."""

import os
from unittest.mock import mock_open, patch

from ..config import Config, get_config


def test_config_from_env_with_bearer_token():
    """Test Config.from_env when BEARER_TOKEN is set."""
    with patch.dict(os.environ, {"API_URL": "http://test-url", "BEARER_TOKEN": "test-token"}):
        config = Config.from_env()
        assert config.api_url == "http://test-url"
        assert config.bearer_token == "test-token"


def test_config_from_env_without_bearer_token():
    """Test Config.from_env when BEARER_TOKEN is not set."""
    with patch.dict(os.environ, {"API_URL": "http://test-url"}):
        config = Config.from_env()
        assert config.api_url == "http://test-url"
        assert config.bearer_token is None


def test_config_from_json_with_bearer_token():
    """Test Config.from_json with bearer_token in JSON."""
    json_content = '{"api_url": "http://test-url", "bearer_token": "test-token", "agents": []}'
    with patch("builtins.open", mock_open(read_data=json_content)):
        config = Config.from_json("fake-path.json")
        assert config.api_url == "http://test-url"
        assert config.bearer_token == "test-token"


def test_config_from_json_without_bearer_token():
    """Test Config.from_json without bearer_token in JSON."""
    json_content = '{"api_url": "http://test-url", "agents": []}'
    with patch("builtins.open", mock_open(read_data=json_content)):
        config = Config.from_json("fake-path.json")
        assert config.api_url == "http://test-url"
        assert config.bearer_token is None


def test_get_config_with_environment_bearer_token():
    """Test get_config uses bearer_token from environment."""
    with patch.dict(os.environ, {"API_URL": "http://test-url", "BEARER_TOKEN": "test-token"}):
        config = get_config()
        assert config.api_url == "http://test-url"
        assert config.bearer_token == "test-token"
