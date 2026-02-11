"""Logging configuration for tekstherkenning_ark.

This module provides a centralized logging configuration that:
- Writes DEBUG level and above to rotating log files
- Writes INFO level and above to stdout (console)
- Uses a consistent format across the application
- Automatically logs uncaught exceptions
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from tekstherkenning_ark.constants import DATA_DIR


# Create logs directory
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file path with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"log_{timestamp}.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Track if we've initialized the root logger
_root_logger_initialized = False


def _ensure_root_logger_configured():
    """Ensure the root logger has handlers for exception logging."""
    global _root_logger_initialized

    if not _root_logger_initialized:
        root_logger = logging.getLogger()

        # Only configure if it doesn't have our handlers yet
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.setLevel(logging.DEBUG)

            # File handler - DEBUG level and above
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10 MB
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
            file_handler.setFormatter(file_formatter)

            # Console handler - INFO level and above
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
            console_handler.setFormatter(console_formatter)

            # Add handlers to root logger
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

        _root_logger_initialized = True


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Name of the logger (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    # Ensure root logger is configured for exception handling
    _ensure_root_logger_configured()

    # Return a logger that will use the root logger's handlers via propagation
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them.

    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
    """
    # Don't log KeyboardInterrupt (Ctrl+C)
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Ensure root logger is configured
    _ensure_root_logger_configured()

    # Get the root logger and log the exception
    logger = logging.getLogger()
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


# Set the exception hook to automatically log uncaught exceptions
sys.excepthook = handle_exception
