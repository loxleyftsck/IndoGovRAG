"""
JDIH Scraper - Production Indonesian Government Legal Document Scraper

Scrapes legal documents from:
  - https://jdih.kemenkumham.go.id  (Kementerian Hukum dan HAM)
  - https://peraturan.go.id         (Peraturan.go.id - JDIH Nasional)

Features:
  - Respects robots.txt and rate limits (max 1 req/sec)
  - Extracts: title, nomor regulasi, tanggal terbit, instansi, PDF URL, status
  - Handles pagination
  - Saves raw metadata to JSON (no PostgreSQL dependency)
  - Document versioning support

Requirements:
  - requests, bs4, pdfplumber (already in requirements.txt)
  - Additional: urllib.robotparser (stdlib)
"""

from __future__ import annotations

import json
import re
import time
import hashlib
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------

# Wrap stdout/stderr with UTF-8 BEFORE basicConfig so the handler inherits it
import io as _io
import sys
if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, _io.TextIOWrapper):
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, _io.TextIOWrapper):
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Data Classes
# ------------------------------------------------------------------------------

class DocumentMetadata:
    """Metadata for a single government regulation document."""

    def __init__(
        self,
        title: str,
        nomor_regulasi: str,
        tahun_terbit: int,
        tanggal_terbit: Optional[str],
        instansi: str,
        pdf_url: Optional[str],
        status: str,
        category: str,
        source_url: str,
        source_name: str,
        version: str = "1.0",
        parent_id: Optional[str] = None,
    ):
        self.title = title
        self.nomor_regulasi = nomor_regulasi
        self.tahun_terbit = tahun_terbit
        self.tanggal_terbit = tanggal_terbit
        self.instansi = instansi
        self.pdf_url = pdf_url
        self.status = status  # "berlaku" | "dicabut" | "diubah"
        self.category = category
        self.source_url = source_url
        self.source_name = source_name
        self.version = version
        self.parent_id = parent_id  # For versioning

    @property
    def doc_id(self) -> str:
        """Stable document ID derived from nomor regulasi."""
        key = f"{self.nomor_regulasi}_{self.tahun_terbit}_{self.instansi}".lower()
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "nomor_regulasi": self.nomor_regulasi,
            "tahun_terbit": self.tahun_terbit,
            "tanggal_terbit": self.tanggal_terbit,
            "instansi": self.instansi,
            "pdf_url": self.pdf_url,
            "status": self.status,
            "category": self.category,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "version": self.version,
            "parent_id": self.parent_id,
            "scraped_at": datetime.utcnow().isoformat() + "Z",
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DocumentMetadata":
        return cls(
            title=d["title"],
            nomor_regulasi=d["nomor_regulasi"],
            tahun_terbit=d["tahun_terbit"],
            tanggal_terbit=d.get("tanggal_terbit"),
            instansi=d["instansi"],
            pdf_url=d.get("pdf_url"),
            status=d.get("status", "berlaku"),
            category=d.get("category", ""),
            source_url=d["source_url"],
            source_name=d.get("source_name", ""),
            version=d.get("version", "1.0"),
            parent_id=d.get("parent_id"),
        )


# ------------------------------------------------------------------------------
# Robots.txt Checker
# ------------------------------------------------------------------------------

class RobotsTxtChecker:
    """Check robots.txt before scraping to respect crawler directives."""

    def __init__(self):
        self._cache: dict[str, requests.PreparedRequest | None] = {}
        self._client = requests.Session()
        self._client.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; IndoGovRAG/1.0; +https://github.com/indogovrag)"
        })

    def can_fetch(self, url: str, base_url: str) -> bool:
        """
        Check if a URL can be fetched based on robots.txt.

        Args:
            url: Full URL to check
            base_url: Base URL of the site (e.g. https://jdih.kemenkumham.go.id)

        Returns:
            True if allowed, False if blocked
        """
        try:
            robots_url = f"{base_url}/robots.txt"
            if robots_url not in self._cache:
                resp = self._client.get(robots_url, timeout=10)
                self._cache[robots_url] = resp.text if resp.status_code == 200 else None

            robots_txt = self._cache[robots_url]
            if not robots_txt:
                return True  # No robots.txt = assume allowed

            from urllib.robotparser import RobotFileParser
            rp = RobotFileParser(robots_url)
            rp.parse(robots_txt.splitlines())
            return rp.can_fetch("*", url)

        except Exception as e:
            logger.debug(f"Robots.txt check failed for {base_url}: {e}")
            return True  # Fail open on errors

    def clear_cache(self):
        """Clear the robots.txt cache."""
        self._cache.clear()


# ------------------------------------------------------------------------------
# Rate Limiter
# ------------------------------------------------------------------------------

class RateLimiter:
    """Simple rate limiter enforcing max 1 request per second."""

    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self._last_request: float = 0.0

    def wait(self):
        """Block until enough time has passed since last request."""
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()


# ------------------------------------------------------------------------------
# Main Scraper
# ------------------------------------------------------------------------------

class JDIHScraper:
    """
    Production scraper for Indonesian government legal documents.

    Sources:
      - jdih.kemenkumham.go.id  (Kementerian Hukum dan HAM)
      - peraturan.go.id           (JDIH Nasional)
    """

    PORTALS = {
        "kemenkumham": {
            "base_url": "https://jdih.kemenkumham.go.id",
            "name": "JDIH Kemenkumham",
            "search_url": "https://jdih.kemenkumham.go.id/produk-hukum",
            "list_selectors": [
                ("div.product-item", None),
                ("div.list-product", None),
                ("div.peraturan-item", None),
                ("table.table-document tr", None),
            ],
            "title_selectors": ["h3.title", "a.title-product", "span.title", "td.judul a"],
            "nomor_selectors": ["span.nomor", "div.nomor", "td.nomor"],
            "tanggal_selectors": ["span.tanggal", "div.tanggal", "td.tanggal"],
            "pdf_selectors": ["a[href$='.pdf']", "a.pdf-download"],
            "status_selectors": ["span.status", "div.status"],
        },
        "peraturan_go_id": {
            "base_url": "https://peraturan.go.id",
            "name": "Peraturan.go.id",
            "search_url": "https://peraturan.go.id/peraturan",
            "list_selectors": [
                ("div.document-list div.item", None),
                ("table.data-table tr", None),
                ("ul.document-list li", None),
            ],
            "title_selectors": ["h2.title", "a.product-name", "span.title"],
            "nomor_selectors": ["span.peraturan-number", "div.nomor", "td.no"],
            "tanggal_selectors": ["span.tanggal-terbit", "div.date"],
            "pdf_selectors": ["a[href$='.pdf']", ".download-pdf a"],
            "status_selectors": ["span.status-indicator"],
        },
    }

    STATUS_KEYWORDS = {
        "berlaku": ["berlaku", "active", "aktif", "still valid"],
        "dicabut": ["dicabut", "tidak berlaku", "expired", "revoked", "diubah dengan"],
        "diubah": ["diubah", "modified", "amended"],
    }

    def __init__(
        self,
        output_dir: str = "data/scraper_output",
        rate_limit: float = 1.0,
        headless: bool = True,
        max_docs_per_portal: int = 100,
    ):
        """
        Initialize scraper.

        Args:
            output_dir: Directory to save JSON metadata files
            rate_limit: Minimum seconds between requests (default 1.0)
            headless: Placeholder for future Selenium integration
            max_docs_per_portal: Maximum docs to scrape per portal
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.rate_limiter = RateLimiter(min_interval=rate_limit)
        self.robots_checker = RobotsTxtChecker()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        })

        self.max_docs = max_docs_per_portal
        self.scraped_count = 0
        self.failed_count = 0
        self._registry: dict[str, DocumentMetadata] = {}

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def scrape_all(self, portals: Optional[list[str]] = None) -> list[DocumentMetadata]:
        """
        Scrape all configured (or specified) portals.

        Args:
            portals: List of portal keys ("kemenkumham", "peraturan_go_id").
                     None = all portals.

        Returns:
            List of DocumentMetadata for all scraped documents.
        """
        if portals is None:
            portals = list(self.PORTALS.keys())

        all_docs = []

        for key in portals:
            if key not in self.PORTALS:
                logger.warning("[SKIP] Unknown portal: %s", key)
                continue

            logger.info("[START] Scraping portal: %s", key)
            portal_config = self.PORTALS[key]

            try:
                docs = self._scrape_portal(key, portal_config)
                all_docs.extend(docs)
                logger.info(
                    "[OK] Scraped %d docs from %s (total: %d)",
                    len(docs), key, self.scraped_count
                )
            except Exception as e:
                logger.error("[ERR] Portal %s failed: %s", key, e)

        # Save to registry
        self._save_registry(all_docs)
        return all_docs

    def scrape_by_category(
        self,
        portal: str,
        category: str,
        max_pages: int = 5,
    ) -> list[DocumentMetadata]:
        """
        Scrape documents from a specific category page.

        Args:
            portal: Portal key
            category: Category slug or query param
            max_pages: Maximum number of pagination pages

        Returns:
            List of scraped documents
        """
        if portal not in self.PORTALS:
            raise ValueError(f"Unknown portal: {portal}")

        config = self.PORTALS[portal]
        docs = []

        for page in range(1, max_pages + 1):
            url = self._build_pagination_url(portal, category, page)
            if not url:
                break

            page_docs = self._scrape_list_page(portal, url, config)
            if not page_docs:
                break  # No more results

            docs.extend(page_docs)
            logger.info("[PAGE] %s page %d: +%d docs", portal, page, len(page_docs))

            if self.scraped_count >= self.max_docs:
                logger.info("[LIMIT] Reached max_docs limit")
                break

        return docs

    def get_document_details(self, doc: DocumentMetadata) -> DocumentMetadata:
        """
        Fetch additional details for a document by visiting its detail page.

        Args:
            doc: Document with at least source_url populated

        Returns:
            Updated DocumentMetadata with more fields filled
        """
        if not doc.source_url:
            return doc

        try:
            self.rate_limiter.wait()
            resp = self.session.get(doc.source_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to extract better metadata from detail page
            detail_text = soup.get_text()

            # Extract tahun if missing
            if not doc.tahun_terbit:
                year_match = re.search(r"(?:tahun|tgl)[\s:]*(\d{4})", detail_text, re.I)
                if year_match:
                    doc.tahun_terbit = int(year_match.group(1))

            # Extract tanggal lengkap
            if not doc.tanggal_terbit:
                date_match = re.search(
                    r"(\d{1,2})\s+(\w+)\s+(\d{4})", detail_text
                ) or re.search(
                    r"(\d{4})-(\d{2})-(\d{2})", detail_text
                )
                if date_match:
                    doc.tanggal_terbit = date_match.group(0)

            # Extract PDF link if not found
            if not doc.pdf_url:
                pdf_links = soup.select("a[href$='.pdf']")
                if pdf_links:
                    doc.pdf_url = self._abs_url(pdf_links[0]["href"], doc.source_url)

        except Exception as e:
            logger.debug("[WARN] Could not fetch details for %s: %s", doc.title, e)

        return doc

    def get_version_history(self, nomor: str, tahun: int) -> list[DocumentMetadata]:
        """
        Find all versions of a regulation by nomor and year.

        Args:
            nomor: Regulation number
            tahun: Year of original regulation

        Returns:
            List of versions (newest first)
        """
        # Check registry for existing docs with same nomor
        versions = [
            doc for doc in self._registry.values()
            if doc.nomor_regulasi == nomor
        ]
        return sorted(versions, key=lambda d: d.scraped_at or "", reverse=True)

    def find_document(self, nomor: str, tahun: Optional[int] = None) -> Optional[DocumentMetadata]:
        """
        Find a specific document by nomor regulasiregulation number.

        Args:
            nomor: Regulation number
            tahun: Optional year filter

        Returns:
            DocumentMetadata or None
        """
        for doc in self._registry.values():
            if doc.nomor_regulasi == nomor:
                if tahun is None or doc.tahun_terbit == tahun:
                    return doc
        return None

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------

    def _scrape_portal(
        self, key: str, config: dict
    ) -> list[DocumentMetadata]:
        """Scrape all pages of a portal."""
        docs = []
        search_url = config["search_url"]

        page = 1
        while page <= 20 and self.scraped_count < self.max_docs:
            url = self._build_pagination_url(key, None, page)
            if not url:
                break

            # Check robots.txt
            if not self.robots_checker.can_fetch(url, config["base_url"]):
                logger.info("[BLOCK] robots.txt blocked: %s", url)
                break

            page_docs = self._scrape_list_page(key, url, config)

            if not page_docs:
                break  # End of pagination

            for doc_meta in page_docs:
                doc = self._enrich_document(doc_meta, config)
                if doc:
                    docs.append(doc)
                    self._registry[doc.doc_id] = doc

            logger.info("[PAGE] %s page %d → +%d docs (total scraped: %d)",
                        key, page, len(page_docs), self.scraped_count)
            page += 1

        return docs

    def _scrape_list_page(
        self, portal_key: str, url: str, config: dict
    ) -> list[DocumentMetadata]:
        """
        Scrape a single list page.

        Returns list of raw DocumentMetadata (without full enrichment).
        """
        try:
            self.rate_limiter.wait()
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()

            # Detect encoding issues
            if resp.apparent_encoding:
                resp.encoding = resp.apparent_encoding

            soup = BeautifulSoup(resp.text, "html.parser")
            docs = []

            # Try each selector pattern
            items = None
            for selector, _ in config["list_selectors"]:
                items = soup.select(selector)
                if items:
                    break

            if not items:
                # Fall back: parse links with PDF href
                links = soup.find_all("a", href=True)
                items = [link.parent for link in links if ".pdf" in link.get("href", "")]

            if not items:
                return []

            for item in items[: self.max_docs]:
                meta = self._extract_from_item(item, config, url)
                if meta:
                    docs.append(meta)

            return docs

        except requests.HTTPError as e:
            logger.error("[HTTP] %s → %s", url, e)
        except Exception as e:
            logger.error("[ERR] Failed to scrape %s: %s", url, e)

        return []

    def _extract_from_item(
        self, item, config: dict, page_url: str
    ) -> Optional[DocumentMetadata]:
        """Extract document metadata from a list item element."""
        try:
            # Title
            title = self._first_text(item, config["title_selectors"]) or item.get_text().strip()
            title = re.sub(r"\s+", " ", title)[:300]

            if not title or len(title) < 5:
                return None

            # Nomor regulasi
            nomor = self._first_text(item, config["nomor_selectors"]) or ""
            nomor = self._clean_nomor(nomor)

            # Tanggal
            tanggal = self._first_text(item, config["tanggal_selectors"]) or ""
            tahun = self._extract_year(tanggal) or datetime.now().year

            # PDF URL
            pdf_url = None
            for sel in config["pdf_selectors"]:
                link = item.select_one(sel)
                if link:
                    href = link.get("href") or link.get("onclick", "")
                    if ".pdf" in str(href):
                        pdf_url = self._abs_url(str(href), page_url)
                        break

            # Status
            status = self._detect_status(item, config.get("status_selectors", []))

            # Category
            category = self._extract_category(page_url)

            return DocumentMetadata(
                title=title,
                nomor_regulasi=nomor or f"UNKNOWN_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                tahun_terbit=tahun,
                tanggal_terbit=tanggal or None,
                instansi=config["name"],
                pdf_url=pdf_url,
                status=status,
                category=category,
                source_url=page_url,
                source_name=config["name"],
            )

        except Exception as e:
            logger.debug("[WARN] Failed to extract item: %s", e)
            return None

    def _enrich_document(
        self, doc: DocumentMetadata, config: dict
    ) -> Optional[DocumentMetadata]:
        """Enrich document with PDF URL and additional metadata."""
        self.scraped_count += 1
        return doc

    def _build_pagination_url(
        self, portal: str, category: Optional[str], page: int
    ) -> Optional[str]:
        """Build paginated list URL for a portal."""
        base = self.PORTALS[portal]["search_url"]

        if "kemenkumham" in portal:
            return f"{base}?page={page}" if page > 1 else base
        elif "peraturan_go_id" in portal:
            if category:
                return f"{base}/{category}?page={page}" if page > 1 else f"{base}/{category}"
            return f"{base}?page={page}" if page > 1 else base

        return None

    def _first_text(self, element, selectors: list[str]) -> Optional[str]:
        """Return text from first matching selector."""
        if not selectors:
            return None
        for sel in selectors:
            found = element.select_one(sel)
            if found:
                text = found.get_text(strip=True)
                if text:
                    return text
        return None

    def _clean_nomor(self, text: str) -> str:
        """Normalize regulation number text."""
        if not text:
            return ""
        text = text.strip()
        # Remove surrounding whitespace and common noise
        text = re.sub(r"^Nomor\s*:?\s*", "", text, flags=re.I)
        return text[:100]

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract 4-digit year from text."""
        if not text:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", text)
        return int(match.group()) if match else None

    def _detect_status(self, element, selectors: list[str]) -> str:
        """Determine document status from text."""
        text = element.get_text().lower()

        for status, keywords in self.STATUS_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return status

        # Fallback: check for revocation patterns
        if "dicabut" in text or "tidak berlaku" in text:
            return "dicabut"
        if "diubah" in text or "amandemen" in text:
            return "diubah"

        return "berlaku"

    def _extract_category(self, url: str) -> str:
        """Infer category from URL path."""
        path = url.split("?")[0]
        parts = path.strip("/").split("/")

        common_cats = ["uu", "perpu", "pp", "perpres", "permen", "kepres",
                       "undang", "peraturan", "produk-hukum", "regulation"]

        for part in parts:
            if part.lower() in common_cats:
                return part.lower().replace("-", " ")

        return parts[-1] if parts else "umum"

    def _abs_url(self, href: str, base: str) -> str:
        """Convert relative href to absolute URL."""
        if not href:
            return ""
        if href.startswith("http"):
            return href
        from urllib.parse import urljoin
        return urljoin(base, href)

    def _save_registry(self, docs: list[DocumentMetadata]):
        """Persist scraped documents to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"registry_{timestamp}.json"

        registry = {
            "scraped_at": datetime.utcnow().isoformat() + "Z",
            "total_documents": len(docs),
            "scraped_count": self.scraped_count,
            "failed_count": self.failed_count,
            "documents": [doc.to_dict() for doc in docs],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

        logger.info("[SAVE] Registry saved → %s (%d docs)", filepath.name, len(docs))

        # Also update "latest" symlink
        latest_path = self.output_dir / "registry_latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------------------------
    # Demo / CLI
    # --------------------------------------------------------------------------

    def run_demo(self, portal: str = "kemenkumham", max_pages: int = 2):
        """
        Run a demo scrape on a single portal.

        Args:
            portal: Portal key to demo
            max_pages: How many pages to scrape
        """
        logger.info("=" * 60)
        logger.info("[DEMO] JDIH Scraper Demo")
        logger.info("Portal: %s | Pages: %d", portal, max_pages)
        logger.info("=" * 60)

        docs = self.scrape_all(portals=[portal])

        logger.info("\n[RESULT] Total docs scraped: %d", len(docs))
        for i, doc in enumerate(docs[:5], 1):
            logger.info(
                "  %d. [%s] %s | %s | %d | %s",
                i, doc.status, doc.nomor_regulasi, doc.title[:60], doc.tahun_terbit, doc.pdf_url or "(no PDF)"
            )

        logger.info("\n[FILE] Saved to: %s/registry_latest.json", self.output_dir)
        return docs


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JDIH Indonesian Government Legal Document Scraper")
    parser.add_argument("--portal", choices=["kemenkumham", "peraturan_go_id", "all"],
                        default="all", help="Which portal to scrape")
    parser.add_argument("--max-docs", type=int, default=50,
                        help="Maximum documents per portal")
    parser.add_argument("--max-pages", type=int, default=10,
                        help="Maximum pages per portal")
    parser.add_argument("--output", default="data/scraper_output",
                        help="Output directory")
    parser.add_argument("--rate-limit", type=float, default=1.0,
                        help="Minimum seconds between requests")

    args = parser.parse_args()

    portals = None if args.portal == "all" else [args.portal]

    scraper = JDIHScraper(
        output_dir=args.output,
        rate_limit=args.rate_limit,
        max_docs_per_portal=args.max_docs,
    )

    docs = scraper.scrape_all(portals=portals)

    print(f"\n✅ Scraping complete: {len(docs)} documents")
    print(f"   Output: {scraper.output_dir}/registry_latest.json")