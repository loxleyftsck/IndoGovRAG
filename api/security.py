"""
Security Middleware for IndoGovRAG API
Rate limiting, authentication, input validation, and audit logging
"""

from fastapi import Request, HTTPException, Security, Header
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import json
from pathlib import Path
from datetime import datetime
import hashlib

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Valid API keys (in production, use database + hashing)
VALID_API_KEYS = {
    "demo-key-12345": {"name": "Demo User", "tier": "free", "limit": "10/minute"},
    "prod-key-67890": {"name": "Production", "tier": "premium", "limit": "100/minute"}
}

# Audit log file
AUDIT_LOG = Path("data/logs/audit.jsonl")
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)

def verify_api_key(api_key: str = Security(api_key_header)) -> dict:
    """
    Verify API key and return user info.
    
    Args:
        api_key: API key from header
    
    Returns:
        User info dict
    
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Add X-API-Key header."
        )
    
    if api_key not in VALID_API_KEYS:
        # Log failed attempt
        audit_log({
            "event": "auth_failure",
            "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:16],
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return VALID_API_KEYS[api_key]

def validate_query_input(question: str) -> None:
    """
    Validate and sanitize query input.
    
    Args:
        question: User query
    
    Raises:
        HTTPException: If input is invalid
    """
    # Length check
    if len(question) < 3:
        raise HTTPException(
            status_code=400,
            detail="Query too short (minimum 3 characters)"
        )
    
    if len(question) > 500:
        raise HTTPException(
            status_code=400,
            detail="Query too long (maximum 500 characters)"
        )
    
    # Injection check (basic)
    dangerous_patterns = ['<script>', 'javascript:', 'onerror=', '<?php']
    for pattern in dangerous_patterns:
        if pattern.lower() in question.lower():
            audit_log({
                "event": "injection_attempt",
                "pattern": pattern,
                "timestamp": datetime.now().isoformat()
            })
            raise HTTPException(
                status_code=400,
                detail="Invalid input detected"
            )

def audit_log(event: dict) -> None:
    """
    Log security and access events.
    
    Args:
        event: Event data to log
    """
    with open(AUDIT_LOG, 'a') as f:
        f.write(json.dumps(event) + '\n')

async def log_request(request: Request, call_next):
    """
    Middleware to log all API requests.
    
    Args:
        request: FastAPI request
        call_next: Next middleware
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency = time.time() - start_time
    
    # Log request
    audit_log({
        "event": "api_request",
        "method": request.method,
        "path": request.url.path,
        "latency": f"{latency:.3f}s",
        "status": response.status_code,
        "timestamp": datetime.now().isoformat(),
        "client": request.client.host if request.client else "unknown"
    })
    
    return response

# Rate limit configuration
RATE_LIMITS = {
    "default": "10/minute",
    "query": "20/minute",
    "health": "100/minute"
}

def get_rate_limit(user_info: dict) -> str:
    """Get rate limit based on user tier."""
    if user_info.get("tier") == "premium":
        return "100/minute"
    return "10/minute"
