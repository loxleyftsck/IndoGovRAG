"""
Advanced Rate Limiter for IndoGovRAG
In-memory sliding window rate limiting

Improvements for A+ security:
- Per-user, per-IP, per-API-key sliding windows
- Burst detection (spike in requests)
- Sliding window (not fixed bucket) for fairness
- Rate limit headers on every response
- Blocked users store (for repeated abuse)
"""

import time
import threading
from typing import Optional, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import hashlib


# ─── Limits ───────────────────────────────────────────────────────────────────

IP_LIMIT = 20          # requests per IP per minute
IP_WINDOW = 60         # seconds

USER_LIMIT = 100       # requests per user_id per minute
USER_WINDOW = 60

API_KEY_LIMIT = 200   # requests per API key per minute
API_KEY_WINDOW = 60

BURST_LIMIT = 5        # max requests per second (burst)
BURST_WINDOW = 1.0     # second window for burst detection


# ─── Abuse Store ─────────────────────────────────────────────────────────────

_ABUSE_STORE: Dict[str, int] = {}   # key → blocked_until timestamp
_ABUSE_LOCK = threading.Lock()

# How many rate-limit hits before temporary block (5 minutes)
_RATELIMIT_HITS_THRESHOLD = 3


@dataclass
class SlidingWindowEntry:
    """Sliding window tracker for a single key (IP/user/API-key)."""
    timestamps: list = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    LIMIT: int = 20
    WINDOW: float = 60.0

    def add_and_check(self, now: float) -> Tuple[bool, int, int]:
        """
        Add a timestamp and immediately check.
        Returns (allowed, remaining, reset_in).
        """
        with self.lock:
            cutoff = now - self.WINDOW
            self.timestamps = [t for t in self.timestamps if t > cutoff]

            if len(self.timestamps) >= self.LIMIT:
                oldest = min(self.timestamps) if self.timestamps else now
                reset_in = max(1, int(oldest + self.WINDOW - now))
                return False, 0, reset_in

            self.timestamps.append(now)
            remaining = self.LIMIT - len(self.timestamps)
            return True, remaining, int(self.WINDOW)

    def count_active(self, now: float) -> int:
        """Return count of requests within window."""
        cutoff = now - self.WINDOW
        return len([t for t in self.timestamps if t > cutoff])

    def prune(self, now: float) -> int:
        cutoff = now - self.WINDOW
        self.timestamps = [t for t in self.timestamps if t > cutoff]
        return len(self.timestamps)


@dataclass
class BurstEntry:
    """Track requests per second for burst detection."""
    times: list = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record_and_check(self, now: float) -> Tuple[bool, int]:
        """
        Returns (allowed, count_in_window).
        """
        with self.lock:
            cutoff = now - BURST_WINDOW
            self.times = [t for t in self.times if t > cutoff]
            if len(self.times) >= BURST_LIMIT:
                return False, len(self.times)
            self.times.append(now)
            return True, len(self.times)


class TieredRateLimiter:
    """
    Tiered in-memory rate limiter.

    Priority (most specific wins):
    1. API key  → 200 req/min
    2. user_id  → 100 req/min
    3. IP       → 20 req/min

    Also tracks:
    - Per-IP burst (5 req/sec max)
    - Abuse score (temp block after repeated violations)
    """

    IP_LIMIT = IP_LIMIT
    USER_LIMIT = USER_LIMIT
    API_KEY_LIMIT = API_KEY_LIMIT

    def __init__(self):
        self._ip_windows: Dict[str, SlidingWindowEntry] = defaultdict(SlidingWindowEntry)
        self._user_windows: Dict[str, SlidingWindowEntry] = defaultdict(SlidingWindowEntry)
        self._api_key_windows: Dict[str, SlidingWindowEntry] = defaultdict(SlidingWindowEntry)
        self._ip_bursts: Dict[str, BurstEntry] = defaultdict(BurstEntry)
        self._rate_limit_hits: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

        # Set limits on default entries
        self._ip_windows["__default__"].LIMIT = IP_LIMIT
        self._ip_windows["__default__"].WINDOW = IP_WINDOW
        self._user_windows["__default__"].LIMIT = USER_LIMIT
        self._user_windows["__default__"].WINDOW = USER_WINDOW
        self._api_key_windows["__default__"].LIMIT = API_KEY_LIMIT
        self._api_key_windows["__default__"].WINDOW = API_KEY_WINDOW

    def _resolve_key(self, key: str, store: Dict) -> SlidingWindowEntry:
        """Get or create an entry with the correct limit config."""
        with self._lock:
            if key not in store:
                store[key] = SlidingWindowEntry(
                    LIMIT=IP_LIMIT if store is self._ip_windows
                    else USER_LIMIT if store is self._user_windows
                    else API_KEY_LIMIT,
                    WINDOW=float(IP_WINDOW if store is self._ip_windows
                                 else USER_WINDOW if store is self._user_windows
                                 else API_KEY_WINDOW),
                )
            return store[key]

    def check_anonymous(self, ip: str) -> Tuple[bool, int, int]:
        """Check rate limit for anonymous IP."""
        now = time.time()
        entry = self._resolve_key(ip, self._ip_windows)

        # Check burst first
        burst = self._ip_bursts.get(ip)
        if burst:
            allowed, _ = burst.record_and_check(now)
            if not allowed:
                reset_in = int(BURST_WINDOW)
                self._record_abuse(ip)
                return False, 0, reset_in

        allowed, remaining, reset_in = entry.add_and_check(now)

        if not allowed:
            self._record_abuse(ip)

        return allowed, remaining, reset_in

    def check_authenticated(self, user_id: str) -> Tuple[bool, int, int]:
        """Check rate limit for authenticated user."""
        now = time.time()
        entry = self._resolve_key(user_id, self._user_windows)
        return entry.add_and_check(now)

    def check_api_key(self, api_key: str) -> Tuple[bool, int, int]:
        """Check rate limit for API key."""
        now = time.time()
        entry = self._resolve_key(api_key, self._api_key_windows)
        return entry.add_and_check(now)

    def _record_abuse(self, key: str) -> None:
        """Track repeated rate limit violations."""
        self._rate_limit_hits[key] += 1
        if self._rate_limit_hits[key] >= _RATELIMIT_HITS_THRESHOLD:
            blocked_until = time.time() + 300  # 5-minute block
            with _ABUSE_LOCK:
                _ABUSE_STORE[key] = blocked_until
            self._rate_limit_hits[key] = 0

    def check(
        self,
        ip: str,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Tuple[bool, int, int, str]:
        """
        Main entry point. Most specific identity wins.

        Returns: (allowed, remaining, reset_in, tier_name)
        """
        # Check abuse block first
        now = time.time()
        for key in [api_key, user_id, ip]:
            if key:
                with _ABUSE_LOCK:
                    blocked_until = _ABUSE_STORE.get(key, 0)
                if blocked_until > now:
                    return False, 0, int(blocked_until - now), "blocked"

        # Tiered check: API key > user_id > IP
        if api_key:
            allowed, remaining, reset_in = self.check_api_key(api_key)
            if allowed:
                return True, remaining, reset_in, "api_key"
            return False, 0, reset_in, "api_key"

        if user_id:
            allowed, remaining, reset_in = self.check_authenticated(user_id)
            if allowed:
                return True, remaining, reset_in, "authenticated"
            return False, 0, reset_in, "authenticated"

        allowed, remaining, reset_in = self.check_anonymous(ip)
        return allowed, remaining, reset_in, "anonymous"

    def get_stats(
        self,
        ip: str,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Return current rate limit statistics for an identity."""
        now = time.time()

        if api_key:
            entry = self._api_key_windows.get(api_key)
            limit, window = API_KEY_LIMIT, API_KEY_WINDOW
            tier = "api_key"
        elif user_id:
            entry = self._user_windows.get(user_id)
            limit, window = USER_LIMIT, USER_WINDOW
            tier = "authenticated"
        else:
            entry = self._ip_windows.get(ip)
            limit, window = IP_LIMIT, IP_WINDOW
            tier = "anonymous"

        if not entry:
            return {"tier": tier, "used": 0, "limit": limit, "window": window, "remaining": limit}

        with entry.lock:
            count = entry.count_active(now)

        return {
            "tier": tier,
            "used": count,
            "limit": limit,
            "window": window,
            "remaining": max(0, limit - count),
        }


# ─── Singleton ─────────────────────────────────────────────────────────────────

rate_limiter = TieredRateLimiter()


# ─── Standard 429 Response ─────────────────────────────────────────────────────

def format_rate_limit_response(
    tier: str,
    remaining: int,
    reset_in: int,
    limit: int,
) -> dict:
    """
    Build the standard JSON response body for HTTP 429.
    """
    messages = {
        "anonymous": "Too many requests from your IP. Please wait and retry.",
        "authenticated": "Too many requests for your account. Please wait and retry.",
        "api_key": "Rate limit reached for your API key. Please wait and retry.",
        "blocked": "Your access has been temporarily suspended due to repeated violations.",
    }

    return {
        "error": "Rate limit exceeded",
        "code": "RATE_LIMIT_EXCEEDED",
        "message": messages.get(tier, "Too many requests."),
        "rate_limit": {
            "tier": tier,
            "limit": limit,
            "remaining": remaining,
            "reset_in_seconds": reset_in,
        },
        "retry_after": reset_in,
    }