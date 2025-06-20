# Agent CLI Tests

This directory contains tests for the Agent CLI utility.

## Running Tests

To run the CLI-specific tests, use:

```bash
# Run from the project root
pytest utils/cli/tests

# Or with more detailed output
pytest utils/cli/tests -v
```

## Test Structure

- `test_config.py` - Tests for the configuration handling (environment variables, JSON, bearer token)
- `test_dotenv.py` - Tests for the .env file loading functionality
- `conftest.py` - Shared fixtures and utilities for CLI tests

## Adding New Tests

When adding new tests:

1. Place them in this directory
2. Use the fixtures defined in `conftest.py` where appropriate
3. Run tests to ensure they pass before committing

Tests are automatically discovered by pytest using the updated `testpaths` configuration in `pyproject.toml`.
