"""
Unit tests for validators
"""

import pytest
from validators import validate_text, validate_context, validate_session_id, validate_batch_request
from errors import ValidationError


def test_validate_text_success():
    """Test successful text validation"""
    text, error = validate_text("Hello world")
    assert error is None
    assert text == "Hello world"


def test_validate_text_empty():
    """Test empty text validation"""
    text, error = validate_text("")
    assert error is not None
    assert error.error_code == "MISSING_TEXT"


def test_validate_text_too_long():
    """Test text that's too long"""
    long_text = "a" * 6000
    text, error = validate_text(long_text)
    assert error is not None
    assert error.error_code == "TEXT_TOO_LONG"


def test_validate_context_success():
    """Test successful context validation"""
    context, error = validate_context({"order_id": "123", "customer_id": "456"})
    assert error is None
    assert context == {"order_id": "123", "customer_id": "456"}


def test_validate_context_invalid():
    """Test invalid context"""
    context, error = validate_context("not a dict")
    assert error is not None
    assert error.error_code == "INVALID_CONTEXT"


def test_validate_session_id_success():
    """Test successful session ID validation"""
    session_id, error = validate_session_id("session-123")
    assert error is None
    assert session_id == "session-123"


def test_validate_session_id_invalid_chars():
    """Test session ID with invalid characters"""
    session_id, error = validate_session_id("session@123")
    assert error is not None
    assert error.error_code == "INVALID_SESSION_ID_FORMAT"


def test_validate_batch_success():
    """Test successful batch validation"""
    texts = ["Hello", "World"]
    validated, error = validate_batch_request(texts)
    assert error is None
    assert len(validated) == 2


def test_validate_batch_too_large():
    """Test batch that's too large"""
    texts = ["text"] * 150
    validated, error = validate_batch_request(texts)
    assert error is not None
    assert error.error_code == "BATCH_TOO_LARGE"

