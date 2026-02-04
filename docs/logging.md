# Logging

## Overview

The tekstherkenning-ark application uses a centralized logging system that provides both file-based and console-based logging.

## Features

- **Dual Output**: 
  - Console (stdout): INFO level and above
  - Log files: DEBUG level and above
  
- **Rotating Log Files**: Automatically rotates when reaching 10MB, keeping 5 backup files

- **Consistent Format**: All logs follow the format:
  ```
  YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message
  ```

## Log Location

Log files are stored in:
```
data/logs/tekstherkenning_ark.log
```

Older log files are automatically rotated with the naming pattern:
- `tekstherkenning_ark.log.1`
- `tekstherkenning_ark.log.2`
- etc.

## Usage

To use logging in a module:

```python
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)

# Then use the logger
logger.debug("Detailed debugging information")
logger.info("General informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Error with full traceback")
```

## Log Levels

- **DEBUG**: Detailed information for diagnosing problems (only in log file)
- **INFO**: Confirmation that things are working as expected (console + file)
- **WARNING**: An indication that something unexpected happened (console + file)
- **ERROR**: A more serious problem (console + file)
- **CRITICAL**: A serious error indicating the program may not continue (console + file)

## Examples

### Caching Operations
```python
logger.info(f"Loading cached Rak from {cache_file}")
logger.info(f"Results cached to: {cache_file.name}")
```

### Warnings
```python
logger.warning(f"Duplicate constructie ID found: {current_constructie_id}")
logger.warning(f"Paal ID {paal_id} not found in rakdeel {self.rakdeel_id}")
```

### Errors
```python
error_msg = "Azure credentials not found in .env file"
logger.error(error_msg)
raise ValueError(error_msg)
```

### Debug Information
```python
logger.debug(f"Token usage: {tokens_number}")
logger.debug(f"Processing paragraph {j+1}")
```

## Changes from Previous Implementation

All `print()` statements in the codebase (excluding `__main__` blocks for testing) have been replaced with appropriate logging calls:

- Informational prints → `logger.info()`
- Warning/duplicate messages → `logger.warning()`
- Error messages before exceptions → `logger.error()`
- Detailed debugging info → `logger.debug()`

This ensures:
1. All application output is properly logged to files
2. Errors are captured in logs for debugging
3. Production deployments have clean console output (INFO level)
4. Developers can enable DEBUG level for detailed troubleshooting
