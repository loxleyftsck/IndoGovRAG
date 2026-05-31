"""
API Key Management Endpoints for IndoGovRAG.

Endpoints:
- GET  /api/keys          - List API keys (authenticated)
- POST /api/keys          - Create new API key (authenticated)
- DELETE /api/keys/{id}   - Deactivate API key (authenticated)

Keys are prefixed with igr_ for easy identification.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from .api_keys import (
    APIKeyManager,
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    api_key_manager,
    require_api_key,
    get_api_key
)


router = APIRouter(prefix="/api", tags=["API Keys"])


@router.get("/keys")
async def list_api_keys(
    key_data: dict = Depends(require_api_key)
) -> dict:
    """
    List all API keys for the authenticated user.

    Requires: X-API-Key header with valid API key
    Returns: List of key metadata (not actual keys)
    """
    user_id = key_data.get("user_id")
    keys = api_key_manager.list_keys(user_id=user_id)

    return {
        "total_keys": len(keys),
        "keys": keys
    }


@router.post("/keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    key_data: dict = Depends(require_api_key)
) -> APIKeyCreateResponse:
    """
    Create a new API key.

    The generated key will be prefixed with 'igr_' for easy identification.
    The full key is only shown ONCE upon creation - it cannot be retrieved later.

    Requires: X-API-Key header with valid API key
    """
    user_id = key_data.get("user_id")

    new_key = api_key_manager.create_key(
        name=request.name,
        tier=request.tier,
        user_id=user_id
    )

    return APIKeyCreateResponse(key=new_key)


@router.delete("/api/keys/{key_id}")
async def deactivate_api_key(
    key_id: str,
    key_data: dict = Depends(require_api_key)
) -> dict:
    """
    Deactivate an API key.

    Requires: X-API-Key header with valid API key
    """
    user_id = key_data.get("user_id")

    # Verify the key belongs to this user
    keys = api_key_manager.list_keys(user_id=user_id)
    key_ids = [k["key_id"] for k in keys]

    if key_id not in key_ids:
        raise HTTPException(
            status_code=404,
            detail="API key not found or not yours"
        )

    success = api_key_manager.deactivate_key(key_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )

    return {"success": True, "message": "API key deactivated"}


@router.get("/api/keys/rate-limits")
async def get_rate_limits() -> dict:
    """
    Get the rate limits for each tier.

    Public endpoint - no authentication required.
    """
    return {
        "tiers": {
            "anonymous": {
                "limit": 20,
                "window_seconds": 60,
                "description": "IP-based, for unauthenticated users"
            },
            "free": {
                "limit": 100,
                "window_seconds": 60,
                "description": "Authenticated free tier"
            },
            "pro": {
                "limit": 100,
                "window_seconds": 60,
                "description": "Pro tier (API key)"
            },
            "enterprise": {
                "limit": 500,
                "window_seconds": 60,
                "description": "Enterprise tier (API key)"
            }
        }
    }
