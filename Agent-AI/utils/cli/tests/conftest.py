"""Fixtures for the CLI tests."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_environment():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, clear=True):
        yield


@pytest.fixture
def mock_dotenv_load():
    """Fixture to mock the dotenv.load_dotenv function."""
    with patch("dotenv.load_dotenv") as mock_load:
        yield mock_load
