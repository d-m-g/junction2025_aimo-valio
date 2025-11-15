"""
Input validation and sanitization
"""

import re
from typing import Dict, Optional, Tuple

from config import config
from errors import ValidationError as NLUValidationError


def validate_text(text: str) -> Tuple[str, Optional[NLUValidationError]]:
    """
    Validate and sanitize input text
    
    Args:
        text: Input text to validate
        
    Returns:
        Tuple of (sanitized_text, error)
    """
    if not text:
        return "", NLUValidationError("Text field is required", "MISSING_TEXT")
    
    if not isinstance(text, str):
        return "", NLUValidationError("Text must be a string", "INVALID_TYPE")
    
    # Trim whitespace
    text = text.strip()
    
    # Check length
    min_length = config.get('validation.min_text_length', 1)
    max_length = config.get('validation.max_text_length', 5000)
    
    if len(text) < min_length:
        return "", NLUValidationError(
            f"Text must be at least {min_length} characters",
            "TEXT_TOO_SHORT"
        )
    
    if len(text) > max_length:
        return "", NLUValidationError(
            f"Text must be at most {max_length} characters",
            "TEXT_TOO_LONG"
        )
    
    # Sanitize: remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace (multiple spaces to single)
    text = re.sub(r' +', ' ', text)
    
    return text, None


def validate_context(context: Optional[Dict]) -> Tuple[Dict, Optional[NLUValidationError]]:
    """
    Validate context object
    
    Args:
        context: Context dictionary
        
    Returns:
        Tuple of (validated_context, error)
    """
    if context is None:
        return {}, None
    
    if not isinstance(context, dict):
        return {}, NLUValidationError("Context must be an object", "INVALID_CONTEXT")
    
    # Validate context keys (allow any keys but check types)
    validated = {}
    for key, value in context.items():
        if not isinstance(key, str):
            return {}, NLUValidationError("Context keys must be strings", "INVALID_CONTEXT_KEY")
        
        # Allow string, number, boolean, or dict values
        if isinstance(value, (str, int, float, bool, dict, list)):
            validated[key] = value
        else:
            return {}, NLUValidationError(
                f"Context value for '{key}' has invalid type",
                "INVALID_CONTEXT_VALUE"
            )
    
    return validated, None


def validate_session_id(session_id: Optional[str]) -> Tuple[Optional[str], Optional[NLUValidationError]]:
    """
    Validate session ID
    
    Args:
        session_id: Session ID string
        
    Returns:
        Tuple of (validated_session_id, error)
    """
    if session_id is None:
        return None, None
    
    if not isinstance(session_id, str):
        return None, NLUValidationError("Session ID must be a string", "INVALID_SESSION_ID")
    
    # Validate format (alphanumeric, dashes, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        return None, NLUValidationError(
            "Session ID contains invalid characters",
            "INVALID_SESSION_ID_FORMAT"
        )
    
    if len(session_id) > 100:
        return None, NLUValidationError(
            "Session ID is too long (max 100 characters)",
            "SESSION_ID_TOO_LONG"
        )
    
    return session_id, None


def validate_batch_request(texts: list) -> Tuple[list, Optional[NLUValidationError]]:
    """
    Validate batch request
    
    Args:
        texts: List of text strings
        
    Returns:
        Tuple of (validated_texts, error)
    """
    if not isinstance(texts, list):
        return [], NLUValidationError("Batch request must be a list", "INVALID_BATCH_FORMAT")
    
    max_batch_size = config.get('validation.max_batch_size', 100)
    if len(texts) > max_batch_size:
        return [], NLUValidationError(
            f"Batch size exceeds maximum of {max_batch_size}",
            "BATCH_TOO_LARGE"
        )
    
    if len(texts) == 0:
        return [], NLUValidationError("Batch request cannot be empty", "EMPTY_BATCH")
    
    validated_texts = []
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            return [], NLUValidationError(
                f"Item {i} in batch is not a string",
                "INVALID_BATCH_ITEM"
            )
        validated, error = validate_text(text)
        if error:
            return [], NLUValidationError(
                f"Item {i} in batch: {error.message}",
                error.error_code
            )
        validated_texts.append(validated)
    
    return validated_texts, None

