"""Tests for logging module."""

import json
import logging

import pytest


def test_json_formatter_formats_as_json() -> None:
    """JSONFormatter should output valid JSON."""
    from groundwork.core.logging import JSONFormatter

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test"
    assert parsed["message"] == "Test message"
    assert "timestamp" in parsed


def test_json_formatter_includes_extra_fields() -> None:
    """JSONFormatter should include extra fields in output."""
    from groundwork.core.logging import JSONFormatter

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.user_id = 42
    record.request_id = "abc123"

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["user_id"] == 42
    assert parsed["request_id"] == "abc123"


def test_get_logger_returns_logger() -> None:
    """get_logger should return a Logger instance."""
    from groundwork.core.logging import get_logger

    logger = get_logger("test.module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"
