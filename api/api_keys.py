"""
API Key Management System for IndoGovRAG.

Simple file-based API key storage with igr_ prefix.
Generate via /api/keys endpoint (authenticated).
"""

import json
import logging
import secrets
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from fastapi import HTTPException, status, Header
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Paths
API_KEYS_FILE = Path(__file__).parent.parent / "config" / "api_keys.json"
API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Ensure file exists
if not API_KEYS_FILE.exists():
    with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)


class APIKeyInfo(BaseModel):
    """API key information model."""
    key: str = Field(..., description="API key (will be prefixed with igr_)")
    name: str = Field(..., description="Friendly name for the key")
    tier: str = Field(default="free", description="Tier: free, pro, or enterprise")
    created_at: str = Field(..., description="ISO timestamp of creation")
    rate_limit: str = Field(..., description="Rate limit like '100/minute'")
    is_active: bool = Field(default=True, description="Whether key is active")


class APIKeyCreateRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Friendly name for the key")
    tier: str = Field(default="free", description="Tier: free, pro, or enterprise")


class APIKeyCreateResponse(BaseModel):
    """Response when creating a new API key."""
    key: str = Field(..., description="The newly created API key (show this to user once!)")


# Rate limits by tier
TIER_LIMITS = {
    "free": "20/minute",
    "pro": "100/minute",
    "enterprise": "500/minute"
}

TIER_REQUEST_LIMITS = {
    "free": 20,
    "pro": 100,
    "enterprise": 500
}


class APIKeyManager:
    """Manage API keys stored in JSON file."""

    def __init__(self):
        self._keys: Dict[str, dict] = {}
        self._load_keys()

    def _load_keys(self):
        """Load keys from file."""
        try:
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                self._keys = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Warning: Failed to load API keys: {e}")
            self._keys = {}

    def _save_keys(self):
        """Save keys to file."""
        try:
            with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._keys, f, indent=2)
            self._load_keys()  # Reload to sync
        except IOError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save API keys: {e}"
            )

    def create_key(self, name: str, tier: str = "free", user_id: Optional[str] = None) -> str:
        """
        Generate a new API key.

        Args:
            name: Friendly name for the key
            tier: Access tier (free, pro, enterprise)
            user_id: Optional user ID for tracking

        Returns:
            The generated API key (igr_...)
        """
        if tier not in TIER_LIMITS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(TIER_LIMITS.keys())}"
            )

        # Generate random key (32 hex chars)
        random_part = secrets.token_hex(16)
        api_key = f"igr_{random_part}"

        # Hash for storage (basic security)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:32]

        # Store metadata
        self._keys[key_hash] = {
            "name": name,
            "tier": tier,
            "created_at": datetime.utcnow().isoformat(),
            "rate_limit": TIER_LIMITS[tier],
            "is_active": True,
            "user_id": user_id
        }

        self._save_keys()
        return api_key

    def validate_key(self, api_key: str) -> Optional[dict]:
        """
        Validate an API key and return its metadata.

        Returns:
            Dict with key metadata if valid, None if invalid
        """
        if not api_key or not api_key.startswith("igr_"):
            return None

        # Hash and look up
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:32]
        key_data = self._keys.get(key_hash)

        if not key_data:
            return None

        if not key_data.get("is_active", True):
            raise HTTPException(
                status_code=403,
                detail="API key has been deactivated"
            )

        return key_data

    def list_keys(self, user_id: Optional[str] = None) -> List[dict]:
        """
        List API keys.
        If user_id is provided, only return keys for that user.
        """
        keys = []
        for key_hash, data in self._keys.items():
            if user_id and data.get("user_id") != user_id:
                continue

            # Don't return the actual key (only show hash)
            keys.append({
                "key_id": key_hash,
                "name": data.get("name"),
                "tier": data.get("tier"),
                "created_at": data.get("created_at"),
                "rate_limit": data.get("rate_limit"),
                "is_active": data.get("is_active", True)
            })

        return keys

    def deactivate_key(self, key_id: str) -> bool:
        """Deactivate an API key by its ID (hash)."""
        if key_id not in self._keys:
            return False

        self._keys[key_id]["is_active"] = False
        self._keys[key_id]["deactivated_at"] = datetime.utcnow().isoformat()
        self._save_keys()
        return True

    def update_tier(self, key_id: str, new_tier: str) -> bool:
        """Update the tier of an API key."""
        if new_tier not in TIER_LIMITS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(TIER_LIMITS.keys())}"
            )

        if key_id not in self._keys:
            return False

        self._keys[key_id]["tier"] = new_tier
        self._keys[key_id]["rate_limit"] = TIER_LIMITS[new_tier]
        self._save_keys()
        return True

    def get_rate_limit(self, api_key: str) -> int:
        """Get the rate limit (requests per minute) for an API key."""
        key_data = self.validate_key(api_key)
        if not key_data:
            return 0

        tier = key_data.get("tier", "free")
        return TIER_REQUEST_LIMITS.get(tier, 20)


# Singleton
api_key_manager = APIKeyManager()


# FastAPI dependency
async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[dict]:
    """
    FastAPI dependency to validate API key from header.
    Returns key metadata if valid, None if not present.
    Raises HTTPException if invalid.
    """
    if not x_api_key:
        return None

    key_data = api_key_manager.validate_key(x_api_key)
    if not key_data:
        raise HTTPException(
            status_code=403,
            detail="Invalid or inactive API key"
        )

    return key_data


async def require_api_key(
    x_api_key: str = Header(..., alias="X-API-Key")
) -> dict:
    """
    FastAPI dependency that requires a valid API key.
    Raises HTTPException if missing or invalid.
    """
    key_data = api_key_manager.validate_key(x_api_key)
    if not key_data:
        raise HTTPException(
            status_code=403,
            detail="Invalid or inactive API key"
        )
    return key_data
