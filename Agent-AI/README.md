# Application Logging

This logging system captures both tool usage and errors. Logs can be configured to be displayed in the console and/or saved to files.

## Log Files

The system creates two main log files in the `logs/` directory:

1. `tool_usage.log`: Records all tool-related activities
   - 🚀 Tool starts
   - ✅ Tool completions
   - ❌ Tool errors
   - 📊 Session summaries

2. `error.log`: Records all application errors
   - Database initialization errors
   - Input processing errors
   - Message parsing errors
   - Stream generation errors
   - Tool execution errors

## Environment Variables

### LOG_CLI

Controls log display in the console/terminal.

- **Default**: `TRUE`
- **Values**:
  - `TRUE`: Display logs in console
  - `FALSE`: Don't display logs in console

```bash
# Disable console logging
export LOG_CLI=FALSE

# Enable console logging (default)
export LOG_CLI=TRUE
```

### LOG_FILES

Controls log writing to files.

- **Default**: `TRUE`
- **Values**:
  - `TRUE`: Write logs to files
  - `FALSE`: Don't write logs to files

```bash
# Disable file logging
export LOG_FILES=FALSE

# Enable file logging (default)
export LOG_FILES=TRUE
```

### LOG_TRUNCATE

Controls tool response truncation in logs.

- **Default**: `TRUE`
- **Values**:
  - `TRUE`: Truncate long responses
  - `FALSE`: Keep complete responses

```bash
# Disable response truncation
export LOG_TRUNCATE=FALSE

# Enable response truncation (default)
export LOG_TRUNCATE=TRUE
```

### LOG_TRUNCATE_LENGTH

Sets the maximum length of responses before truncation.

- **Default**: `100`
- **Values**: Any positive integer
- **Note**: Only used if LOG_TRUNCATE=TRUE

```bash
# Set a 500-character limit
export LOG_TRUNCATE_LENGTH=500

# Return to default limit
export LOG_TRUNCATE_LENGTH=100
```

### Combined Usage Examples

```bash
# Complete logs in files only
export LOG_CLI=FALSE
export LOG_FILES=TRUE
export LOG_TRUNCATE=FALSE

# Logs truncated to 200 characters everywhere
export LOG_CLI=TRUE
export LOG_FILES=TRUE
export LOG_TRUNCATE=TRUE
export LOG_TRUNCATE_LENGTH=200

# Console-only, very short logs
export LOG_CLI=TRUE
export LOG_FILES=FALSE
export LOG_TRUNCATE=TRUE
export LOG_TRUNCATE_LENGTH=50
```

## Log Format

All logs follow this format:
```
{timestamp} - {level} - {emoji} {type} | {context}
```

Examples:
```
2024-03-21 10:30:15 - INFO - 🚀 TOOL_START | Thread: abc123 | Tool: search_tool
2024-03-21 10:30:16 - INFO - ✅ TOOL_COMPLETE | Thread: abc123 | Tool: search_tool | Response: Result... (truncated, full length: 256)
2024-03-21 10:30:16 - ERROR - ❌ ERROR | Type: Database Error | Message: Connection failed
```

## Security Note

If you disable file logging (`LOG_FILES=FALSE`), no log files will be created. However, it's recommended to keep at least one type of logging active for debugging and system monitoring.

For sensitive or confidential responses, you can:
1. Disable truncation to see complete responses: `LOG_TRUNCATE=FALSE`
2. Increase truncation length: `LOG_TRUNCATE_LENGTH=1000`
3. Use file logging only: `LOG_CLI=FALSE`

## Configuration Status

You can check the current logging configuration status programmatically:

```python
from app.logger import get_logging_status

status = get_logging_status()
print(status)
# Output:
# {
#     "console_logging": True,
#     "file_logging": True,
#     "truncate_responses": True,
#     "truncate_length": 100
# }
```

## Log Directory Structure

```
logs/
├── tool_usage.log  # Tool-related activities
└── error.log      # Application errors
```

## Best Practices

1. **Development Environment**
   ```bash
   export LOG_CLI=TRUE
   export LOG_FILES=TRUE
   export LOG_TRUNCATE=FALSE  # See complete responses for debugging
   ```

2. **Production Environment**
   ```bash
   export LOG_CLI=TRUE      # Reduce console noise
   export LOG_FILES=FALSE     # Keep file logs for monitoring
   export LOG_TRUNCATE=FALSE  # Save disk space
   ```

3. **Debug Mode**
   ```bash
   export LOG_CLI=TRUE
   export LOG_FILES=TRUE
   export LOG_TRUNCATE=TRUE
   export LOG_TRUNCATE_LENGTH=1000  # See more context
   ```
