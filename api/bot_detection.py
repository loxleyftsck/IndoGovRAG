"""
Bot Detection & Request Fingerprinting for IndoGovRAG

Features:
- Request fingerprinting (IP + UA + Accept-Language + query hash)
- Honeypot field detection (hidden form fields that bots fill)
- Anomaly scoring (multiple signals, weighted)
- Bot verdict with signals breakdown

OWASP Top 10 coverage:
- A01: Broken Access Control (fingerprinting ties requests to identity)
- A03: Injection (prevention middleware)
- A05: Security Misconfiguration (bot detection for automated attacks)
- A10: Automated Threats (bot detection layer)
"""

import hashlib
import re
import time
import threading
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict
from fastapi import Request


# ─── Honeypot Field Names ──────────────────────────────────────────────────────

# These fields should NEVER be filled by a real human user.
# If any of these appears in a request body, it's a bot.
HONEYPOT_FIELD_NAMES = frozenset([
    "__hp",          # hidden honeypot
    "__captcha",     # fake captcha
    "__anti_bot",    # anti-bot trap
    "__csrf_token",  # fake CSRF (real CSRF is handled separately)
    "website_url",   # common Contact-form honeypot
    "url",           # another common honeypot
    "homepage",      # email form honeypot
    "subject",       # email form honeypot
    "message",       # redundant with query (another honeypot)
    "_wpnonce",      # WordPress nonce trap
    "百姓",          # Chinese honeypot (gibberish to Indonesian context)
    "联系方式",       # Chinese contact trap
])

# Known bot UA substrings
BOT_UA_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"bot", r"crawler", r"spider", r"scraper", r"curl", r"wget",
        r"python-requests", r"axios", r"fetch", r"httpie", r"postman",
        r"selenium", r"playwright", r"puppeteer", r"headless",
        r"scrape", r"scan", r"index", r"slurp", r"baiduspider",
        r"yandex", r"duckduckbot", r"bingbot", r"googlebot",
        r"semrush", r"ahrefs", r"mj12bot", r"dotbot",
        r"chrome-lighthouse", r"lighthouse", r"pagespeed",
    ]
]

# Suspicious request patterns (anomaly signals)
SUSPICIOUS_QUERY_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"union\s+select",          # SQL injection
        r"<script",                 # XSS
        r"\.\./",                   # Path traversal
        r"\x00",                    # Null byte
        r"%0a",                     # URL newline injection
        r"%0d%0a",                  # CRLF injection
        r"eval\s*\(",               # Code injection
        r"base64_decode",           # PHP encoded injection
        r"concat\s*\(",             # SQL concat
        r"waitfor\s+delay",         # SQL time-based
    ]
]


# ─── Fingerprint Store (sliding window) ──────────────────────────────────────

_fingerprint_store: dict = {}
_fingerprint_lock = threading.Lock()
_FINGERPRINT_WINDOW = 60   # seconds
_MAX_FINGERPRINT_REQUESTS = 30  # per fingerprint per minute


@dataclass
class FingerprintEntry:
    """Track request count per fingerprint."""
    count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, now: float) -> int:
        """Record a request. Returns current count."""
        with self.lock:
            self.count += 1
            self.last_seen = now
            return self.count


def _get_fingerprint_entry(fingerprint: str) -> FingerprintEntry:
    with _fingerprint_lock:
        if fingerprint not in _fingerprint_store:
            _fingerprint_store[fingerprint] = FingerprintEntry()
        return _fingerprint_store[fingerprint]


def _prune_fingerprints(now: float) -> None:
    """Remove stale fingerprint entries."""
    cutoff = now - _FINGERPRINT_WINDOW
    with _fingerprint_lock:
        stale = [k for k, v in _fingerprint_store.items() if v.last_seen < cutoff]
        for k in stale:
            del _fingerprint_store[k]


# ─── Bot Detection Result ────────────────────────────────────────────────────

@dataclass
class BotDetectionResult:
    """Result of bot detection analysis."""
    is_bot: bool
    score: float          # 0.0 = definitely human, 1.0 = definitely bot
    signals: list[str]   # human-readable list of triggered signals
    fingerprint: str


# ─── Request Fingerprinting ──────────────────────────────────────────────────

def build_fingerprint(request: Request) -> str:
    """
    Build a stable, collision-resistant fingerprint for a request.

    Combines:
    - Client IP (or x-forwarded-for)
    - User-Agent hash
    - Accept-Language hash
    - First 50 chars of query string hash

    Returns a 32-char hex string.
    """
    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    ua = request.headers.get("user-agent", "")
    lang = request.headers.get("accept-language", "")
    query = str(request.url.query)[:50]

    raw = f"{ip}|{ua}|{lang}|{query}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


# ─── Bot Detection ───────────────────────────────────────────────────────────

def is_bot_request(request: Request, fingerprint: str) -> BotDetectionResult:
    """
    Multi-signal bot detection.

    Signals checked:
    1. Known bot User-Agent
    2. Honeypot fields in request body
    3. Suspicious query patterns
    4. Fingerprint burst (same fingerprint making too many requests)
    5. Missing Accept-Language (unusual for real browser)
    6. Missing Accept header (unusual for real browser)
    7. Very long User-Agent (often bot-generated)
    """
    signals: list[str] = []
    score = 0.0

    # ── Signal 1: Known bot UA ──
    ua = request.headers.get("user-agent", "")
    for pattern in BOT_UA_PATTERNS:
        if pattern.search(ua):
            signals.append(f"bot_ua:{pattern.pattern}")
            score += 0.5
            break

    # ── Signal 2: Honeypot fields ──
    # Note: This is checked against the raw query params.
    # In FastAPI, we check query params and can check body in endpoints.
    query = request.url.query.lower()
    for field_name in HONEYPOT_FIELD_NAMES:
        if field_name.lower() in query:
            signals.append(f"honeypot:{field_name}")
            score += 0.8  # Strong signal

    # ── Signal 3: Suspicious query patterns ──
    for pattern in SUSPICIOUS_QUERY_PATTERNS:
        if pattern.search(query):
            signals.append(f"suspicious_query:{pattern.pattern}")
            score += 0.6
            break

    # ── Signal 4: Fingerprint burst ──
    now = time.time()
    _prune_fingerprints(now)
    entry = _get_fingerprint_entry(fingerprint)
    count = entry.record(now)

    if count > _MAX_FINGERPRINT_REQUESTS:
        signals.append(f"fingerprint_burst:{count}")
        score += 0.4

    # ── Signal 5: Missing Accept-Language ──
    if not request.headers.get("accept-language"):
        signals.append("missing_accept_language")
        score += 0.1

    # ── Signal 6: Missing Accept header ──
    if not request.headers.get("accept"):
        signals.append("missing_accept")
        score += 0.1

    # ── Signal 7: Abnormally long User-Agent ──
    if len(ua) > 500:
        signals.append(f"long_ua:{len(ua)}")
        score += 0.2

    # ── Signal 8: Empty User-Agent ──
    if not ua:
        signals.append("empty_ua")
        score += 0.15

    # ── Bot verdict ──
    # score >= 0.5 → bot (or very suspicious)
    # Honeypot field alone triggers bot
    is_bot = score >= 0.5

    return BotDetectionResult(
        is_bot=is_bot,
        score=min(score, 1.0),
        signals=signals,
        fingerprint=fingerprint,
    )


# ─── Honeypot Field Extractor ─────────────────────────────────────────────────

def extract_honeypot_fields(query_params: dict) -> list[str]:
    """
    Check a dict of query/body parameters for honeypot fields.
    Returns list of honeypot field names found.
    """
    found = []
    for key in query_params:
        key_lower = key.lower()
        if key_lower in HONEYPOT_FIELD_NAMES:
            found.append(key)
        # Also catch obfuscated honeypots (e.g., __hp with spaces)
        if key_lower.strip().replace(" ", "") in HONEYPOT_FIELD_NAMES:
            found.append(key)
    return found


# ─── XXE Pattern Detector ─────────────────────────────────────────────────────

XXE_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"<!DOCTYPE[^>]*\[.*?\]>",   # DOCTYPE with internal subset
        r"<!ENTITY",                   # Entity declaration
        r"&#\d+;",                    # Decimal numeric entity
        r"&#x[0-9a-fA-F]+;",          # Hex numeric entity
        r"%#[0-9]+;",                  # Parameter entity decimal
        r"%#[xX][0-9a-fA-F]+;", # Parameter entity hex
        r"file:///etc",               # File inclusion attempt
        r"php://input",              # PHP wrapper abuse
        r"expect://", # PHP expect wrapper
        r"data:text/html",           # Data URI abuse
    ]
]


def contains_xxe(text: str) -> bool:
    """Check if text contains XXE patterns."""
    for pattern in XXE_PATTERNS:
        if pattern.search(text):
            return True
    return False
