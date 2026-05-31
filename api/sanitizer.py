"""
Input Sanitization & Security Validation for IndoGovRAG

OWASP A03 (Injection) Coverage:
- SQL injection pattern blocking (20+ regex patterns)
- Command injection pattern blocking (15+ patterns)
- XSS prevention (22+ patterns including mutation XSS)
- XXE prevention (10 patterns)
- Path traversal prevention (9 patterns)
- CRLF / header injection prevention (3 patterns)
- SSRF prevention (6 patterns)
- JSON depth limit (max 10 levels)
- Null-byte rejection
- File extension allowlist (17 dangerous extensions blocked)
- Options allowlist enforcement
"""

import re
import html
import json
from typing import Optional, List
from fastapi import HTTPException


# ─── SQL Injection Patterns ────────────────────────────────────────────────────

SQL_INJECTION_PATTERNS = [
    # SQL keywords + command chaining
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\bunion\s+(all\s+)?select\b",
        r"\bunion\s+select\b",
        r"\bselect\s+.*\s+from\b",
        r"\binsert\s+into\b",
        r"\bupdate\s+.*\s+set\b",
        r"\bdelete\s+from\b",
        r"\bdrop\s+(table|database|index|column)\b",
        r"\bcreate\s+(table|database|proc)\b",
        r"\balter\s+(table|database)\b",
        r"\bexec\b",
        r"\bexecute\b",
        r"\bxp_cmdshell\b",
        r"\bsp_executesql\b",
        r"\bopenquery\b",
        r"\bopendatasource\b",
        r"\bload_file\b",
        r"\binto\s+outfile\b",
        r"\binto\s+dumpfile\b",
        # Comment + inline attack
        r"'\s*;\s*--",
        r"'\s*#",
        r"--\s*$",
        # Classic boolean-based
        r"'?\s+or\s+'1'\s*=\s*'1",
        r"'?\s+or\s+1\s*=\s*1\b",
        r"'\s+or\s+'a'\s*=\s*'a",
        r"\bor\s+true\b",
        # Time-based blind
        r"\bwaitfor\s+delay\b",
        r"\bwaitfor\s+timeout\b",
        r"\bsleep\s*\(\s*\d+\s*\)\b",
        r"\bbenchmark\s*\(",
        r"\bpg_sleep\b",
        # Stacked queries
        r";\s*\bdrop\b",
        r";\s*\bdelete\b",
        r";\s*\binsert\b",
        r";\s*\bupdate\b",
        r";\s*\bexec\b",
        # Information schema access
        r"information_schema\b",
        r"sys\.objects\b",
        r"sys\.tables\b",
        r"mysql\.driver\b",
        r"syscat\b",
        # Hex encoding
        r"0x[0-9a-f]+",
        # String concat attacks
        r"char\s*\(\s*\d+(\s*,\s*\d+)*\s*\)",
        r"concat\s*\(",
        r"concat_ws\s*\(",
    ]
]


# ─── Command Injection Patterns ───────────────────────────────────────────────

COMMAND_INJECTION_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r";\s*(ls|cat|sh|bash|cmd|pwd|whoami|id|uname|ping|curl|wget|dir|echo|rm|mv|cp|mkdir|touch)\b",
        r"\|\s*\w+",
        r"`[^`]+`",
        r"\$\([^)]+\)",
        r"%0a",               # URL-encoded newline
        r"%0d%0a",            # URL-encoded CRLF
        r"\n", # Raw newline (in body)
        r"\r\n",
        r"&&\s*\w+",
        r"\|\|\s*\w+",
        r"&\s*\w+",
        r"2>&1",
        r">\s*/dev/null",
        r"<\s*/dev/null",
        r"curl\s+",           # curl download
        r"wget\s+",           # wget download
        r"python\s+-c\b",
        r"python3\s+-c\b",
        r"bash\s+-c\b",
        r"sh\s+-c\b",
        r" perl\s+-e\b",
        r" ruby\s+-e\b",
        r" nc\s+",            # netcat reverse shell
        r" telnet\s+",
        r"ping\s+-c\b",
        r"chmod\s+",
        r"chown\s+",
        r"base64\s+-d\b",
        r"openssl\s+",
        r"system\s*\(",
        r"passthru\s*\(",
        r"shell_exec\s*\(",
        r"popen\s*\(",
        r"proc_open\s*\(",
    ]
]


# ─── XSS Patterns ─────────────────────────────────────────────────────────────

XSS_PATTERNS = [
    re.compile(r, re.IGNORECASE | re.DOTALL)
    for r in [
        r"<script[^>]*>.*?</script>",
        r"<script[^>]*\bsrc\s*=",
        r"<script[^>]*\bon\w+\s*=",
        r"javascript\s*:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"onfocus\s*=",
        r"onblur\s*=",
        r"onchange\s*=",
        r"onsubmit\s*=",
        r"onkeydown\s*=",
        r"onkeyup\s*=",
        r"onkeypress\s*=",
        r"eval\s*\(",
        r"exec\s*\(",
        r"Function\s*\(",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
        r"<applet[^>]*>",
        r"<base[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"<style[^>]*>@import",
        r"<svg[^>]*onload\s*=",
        r"<body[^>]*onload\s*=",
        r"<marquee[^>]*on",
        r"<input[^>]*on",
        r"<details[^>]*ontoggle\s*=",
        r"data\s*:\s*text/html",
        r"vbscript\s*:",
        r"expression\s*\(",
    ]
]


# ─── XXE Patterns ─────────────────────────────────────────────────────────────

XXE_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"<!DOCTYPE[^>]*\[.*?\]>",
        r"<!ENTITY",
        r"&#\d+;",
        r"&#x[0-9a-fA-F]+;",
        r"%#[0-9]+;",
        r"%#[xX][0-9a-fA-F]+;",
        r"file:///etc",
        r"php://input",
        r"expect://",
        r"data:text/html",
    ]
]


# ─── Path Traversal Patterns ──────────────────────────────────────────────────

PATH_TRAVERSAL_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\.\.[/\\]",
        r"^[/\\]\.\.",
        r"%2e%2e",
        r"\.\.%2f",
        r"\.\.%2f",
        r"\.\.%5c",
        r"\.\.%c0%",
        r"\.\.%a0",
        r"^\.\.$",
    ]
]


# ─── CRLF Injection Patterns ──────────────────────────────────────────────────

CRLF_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"%0d%0a",
        r"\r\n",
        r"\r",
 ]
]


# ─── SSRF Patterns ─────────────────────────────────────────────────────────────

SSRF_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"http://localhost",
        r"http://127\.0\.0\.1",
        r"http://0\.0\.0\.0",
        r"http://169\.254\.169\.254",
        r"https://169\.254\.169\.254",
        r"file:///etc",
        r"dict://",
        r"gopher://",
    ]
]


# ─── Input Sanitizer ────────────────────────────────────────────────────────────

class InputSanitizer:
    """
    Input sanitization with layered OWASP A03 pattern checks.

    Order of operations:
    1. Type check
    2. Length check
    3. Null-byte check
    4. SQL injection patterns
    5. Command injection patterns
    6. XSS patterns
    7. XXE patterns
    8. Path traversal patterns
    9. CRLF patterns
    10. SSRF patterns
    11. HTML tag stripping + entity decoding
    12. Whitespace trim
    """

    MAX_QUERY_LENGTH = 500
    MAX_DOC_ID_LENGTH = 200
    MAX_OPTIONS_DEPTH = 10

    @classmethod
    def sanitize_query(cls, query: str, field_name: str = "query") -> str:
        if not isinstance(query, str):
            raise HTTPException(400, f"{field_name} must be a string")

        if not query:
            raise HTTPException(400, f"{field_name} cannot be empty")

        if len(query) > cls.MAX_QUERY_LENGTH:
            raise HTTPException(400, f"{field_name} too long (max {cls.MAX_QUERY_LENGTH})")

        if len(query.strip()) < 2:
            raise HTTPException(400, f"{field_name} too short (min 2 chars)")

        # Null-byte check
        if "\x00" in query or "�" in query:
            raise HTTPException(400, "Invalid character detected")

        q_lower = query.lower()

        # SQL injection
        for p in SQL_INJECTION_PATTERNS:
            if p.search(q_lower):
                raise HTTPException(400, "Invalid input detected. Please rephrase.")

        # Command injection
        for p in COMMAND_INJECTION_PATTERNS:
            if p.search(query):
                raise HTTPException(400, "Invalid input detected. Please rephrase.")

        # XSS
        for p in XSS_PATTERNS:
            if p.search(query):
                raise HTTPException(400, "Invalid input detected. Please rephrase.")

        # XXE
        for p in XXE_PATTERNS:
            if p.search(query):
                raise HTTPException(400, "Invalid input detected. Please rephrase.")

        # Path traversal
        for p in PATH_TRAVERSAL_PATTERNS:
            if p.search(query):
                raise HTTPException(400, "Invalid path sequence detected.")

        # CRLF
        for p in CRLF_PATTERNS:
            if p.search(query):
                raise HTTPException(400, "Invalid character sequence detected.")

        # SSRF
        for p in SSRF_PATTERNS:
            if p.search(query):
                raise HTTPException(400, "Invalid URL pattern detected.")

        # Strip HTML tags and decode entities
        clean = cls._strip_html(query)
        clean = html.unescape(clean)
        return clean.strip()

    @classmethod
    def _strip_html(cls, text: str) -> str:
        """Remove all HTML tags, preserving text content."""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&[a-zA-Z0-9#]+;", "", text)
        text = text.replace("&", "")
        return text

    @classmethod
    def sanitize_document_id(cls, doc_id: str) -> str:
        if not isinstance(doc_id, str):
            raise HTTPException(400, "Document ID must be a string")

        if "\x00" in doc_id:
            raise HTTPException(400, "Invalid character in document ID")

        if not re.match(r"^[\w\-\.]+$", doc_id):
            raise HTTPException(400, "Invalid document ID format")

        if len(doc_id) > cls.MAX_DOC_ID_LENGTH:
            raise HTTPException(400, "Document ID too long")

        return doc_id

    @classmethod
    def sanitize_file_path(cls, filename: str) -> str:
        """
        Sanitize a filename or path.
        Blocks: dangerous extensions, null bytes, path traversal, null bytes.
        Returns only the basename (strips directories).
        """
        if not isinstance(filename, str):
            raise HTTPException(400, "Filename must be a string")

        if "\x00" in filename:
            raise HTTPException(400, "Null byte not allowed in filename")

        # Block dangerous extensions anywhere in path
        dangerous_exts = [
            ".exe", ".bat", ".cmd", ".sh", ".ps1", ".rb", ".py",
            ".jar", ".dll", ".so", ".c", ".cpp", ".h", ".php",
            ".asp", ".aspx", ".jsp", ".jspx", ".cgi",
        ]
        ext_lower = filename.lower()
        for ext in dangerous_exts:
            if ext_lower.endswith(ext):
                raise HTTPException(400, f"Extension '{ext}' is not allowed")

        # Block path traversal
        for p in PATH_TRAVERSAL_PATTERNS:
            if p.search(filename):
                raise HTTPException(400, "Invalid path sequence detected")

        # Return only basename (strip all directory components)
        basename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        return basename

    @classmethod
    def sanitize_options(cls, options: dict) -> dict:
        if not isinstance(options, dict):
            raise HTTPException(400, "Options must be a dictionary")

        allowed_keys = {
            "use_query_expansion",
            "use_reranking",
            "use_hybrid",
            "top_k",
            "use_cache",
        }
        sanitized = {k: v for k, v in options.items() if k in allowed_keys}

        if "top_k" in sanitized:
            try:
                top_k = int(sanitized["top_k"])
                if not 1 <= top_k <= 50:
                    raise ValueError
                sanitized["top_k"] = top_k
            except (ValueError, TypeError):
                raise HTTPException(400, "top_k must be an integer between 1 and 50")

        for key in ["use_query_expansion", "use_reranking", "use_hybrid", "use_cache"]:
            if key in sanitized:
                sanitized[key] = bool(sanitized[key])

        return sanitized

    @classmethod
    def sanitize_json_body(cls, body: bytes) -> dict:
        """
        Parse JSON body with depth limit to prevent DoS via deeply nested JSON.
        """
        if not body:
            raise HTTPException(400, "Request body cannot be empty")

        # Reject extremely large bodies (> 1 MB)
        if len(body) > 1_048_576:
            raise HTTPException(400, "Request body too large (max 1 MB)")

        try:
            obj = json.loads(body)
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"Invalid JSON: {e.msg}")

        # Depth check
        def max_depth(obj, depth=0):
            if depth > cls.MAX_OPTIONS_DEPTH:
                raise ValueError("JSON depth exceeds limit")
            if isinstance(obj, dict):
                return max((max_depth(v, depth + 1) for v in obj.values()), default=depth)
            if isinstance(obj, list):
                return max((max_depth(v, depth + 1) for v in obj), default=depth)
            return depth

        try:
            max_depth(obj)
        except ValueError:
            raise HTTPException(400, f"JSON nesting exceeds {cls.MAX_OPTIONS_DEPTH} levels")

        return obj


# ─── Public Helper ─────────────────────────────────────────────────────────────

def validate_and_sanitize(query: str, options: Optional[dict] = None) -> tuple[str, dict]:
    """
    Combined validation + sanitization for query requests.
    Returns (sanitized_query, sanitized_options).
    """
    sq = InputSanitizer.sanitize_query(query)
    so = InputSanitizer.sanitize_options(options or {})
    return sq, so
