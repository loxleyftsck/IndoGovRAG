"""
Error Handling Module for IndoGovRAG
Provides standardized error types and Indonesian error messages.
"""

from .schemas import (
    ErrorType,
    ErrorResponse,
    error_responses,
    get_error_response,
    create_error_response,
    create_success_response,
    create_fallback_response,
    check_confidence_warnings,
    check_chunk_count_warning,
    check_superseded_document,
    LOW_CONFIDENCE_THRESHOLD,
    SUPERSEDED_WARNING_BANNER,
)

__all__ = [
    'ErrorType',
    'ErrorResponse',
    'error_responses',
    'get_error_response',
    'create_error_response',
    'create_success_response',
    'create_fallback_response',
    'check_confidence_warnings',
    'check_chunk_count_warning',
    'check_superseded_document',
    'LOW_CONFIDENCE_THRESHOLD',
    'SUPERSEDED_WARNING_BANNER',
]
