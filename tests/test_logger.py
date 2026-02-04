"""
Test Logger Module

Tests the logging functionality including automatic exception logging.
"""

import logging
import pytest
import sys
from pathlib import Path
from tekstherkenning_ark.logger import get_logger, handle_exception


def test_exception_handler_logs_error(caplog):
    """Test that the exception handler logs uncaught exceptions."""
    # Create a test exception
    exc_type = ValueError
    exc_value = ValueError("Test error message")
    exc_traceback = None

    # Capture logs at CRITICAL level
    with caplog.at_level(logging.CRITICAL):
        handle_exception(exc_type, exc_value, exc_traceback)

    # Check that the exception was logged
    assert len(caplog.records) > 0
    assert "Uncaught exception" in caplog.text
    assert "ValueError" in caplog.text


def test_logger_captures_raised_exceptions(caplog):
    """Test that raised exceptions are captured by the logger when uncaught."""
    # This test simulates what happens when an exception is raised
    # In practice, sys.excepthook would catch it

    def raise_error():
        raise ValueError("This is a test error")

    # Manually trigger the exception handler
    try:
        raise_error()
    except ValueError as e:
        import traceback

        exc_info = sys.exc_info()

        with caplog.at_level(logging.CRITICAL):
            handle_exception(exc_info[0], exc_info[1], exc_info[2])

        # Verify the exception was logged
        assert "Uncaught exception" in caplog.text
        assert "This is a test error" in caplog.text
