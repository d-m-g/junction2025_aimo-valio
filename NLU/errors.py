"""
Error handling and error codes
"""

from typing import Dict, Optional


class NLUError(Exception):
    """Base NLU error"""
    def __init__(self, message: str, error_code: str, status_code: int = 400, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        """Convert error to dictionary"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(NLUError):
    """Validation error"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        super().__init__(message, error_code, 400, details)


class ParseError(NLUError):
    """Parsing error"""
    def __init__(self, message: str, error_code: str = 'PARSE_ERROR', details: Optional[Dict] = None):
        super().__init__(message, error_code, 422, details)


class InternalError(NLUError):
    """Internal server error"""
    def __init__(self, message: str, error_code: str = 'INTERNAL_ERROR', details: Optional[Dict] = None):
        super().__init__(message, error_code, 500, details)


# Error code constants
ERROR_CODES = {
    'MISSING_TEXT': 'Text field is required',
    'INVALID_TYPE': 'Invalid data type',
    'TEXT_TOO_SHORT': 'Text is too short',
    'TEXT_TOO_LONG': 'Text is too long',
    'INVALID_CONTEXT': 'Invalid context format',
    'INVALID_SESSION_ID': 'Invalid session ID',
    'PARSE_ERROR': 'Error parsing input',
    'INTERNAL_ERROR': 'Internal server error',
    'BATCH_TOO_LARGE': 'Batch size exceeds limit',
    'EMPTY_BATCH': 'Batch request is empty',
    'INVALID_BATCH_FORMAT': 'Invalid batch request format',
    'INVALID_BATCH_ITEM': 'Invalid item in batch',
}

