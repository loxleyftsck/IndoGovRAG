"""
Pipeline Scheduler - Automated cron-based document processing

Features:
  - Weekly cron job that checks for new documents
  - Re-indexes only changed/new documents (versioning support)
  - Sends notification on completion with counts
  - State persistence to track processed documents
  - Email/webhook notification support (configurable)

Requirements:
  - Python cron scheduler (using APScheduler)
  - State file for tracking processed documents
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Import our pipeline components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.jdih_scraper import JDIHScraper
from pipeline.chunker import PipelineChunker
from pipeline.embedder import PipelineEmbedder

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------

# Wrap stdout/stderr with UTF-8 BEFORE basicConfig so the handler inherits it
import io as _io
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
# State Tracking
# ------------------------------------------------------------------------------

class PipelineState:
    """Track processed documents for incremental updates."""

    def __init__(self, state_path: str = "data/pipeline/state.json"):
        """
        Initialize state tracker.

        Args:
            state_path: Path to state JSON file
        """
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        self.state: dict = self._load()
        self.state.setdefault("last_run", None)
        self.state.setdefault("processed_docs", {})  # doc_id -> hash
        self.state.setdefault("version_history", {})  # doc_id -> [version1, version2, ...]
        self.state.setdefault("stats", {
            "total_runs": 0,
            "total_processed": 0,
            "total_new": 0,
            "total_updated": 0,
            "last_error": None,
        })

    def _load(self) -> dict:
        """Load state from disk."""
        if self.state_path.exists():
            try:
                with open(self.state_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("[WARN] Could not load state: %s. Starting fresh.", e)
        return {}

    def save(self):
        """Save state to disk."""
        self.state["last_run"] = datetime.utcnow().isoformat() + "Z"

        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def is_processed(self, doc_id: str, content_hash: str) -> tuple[bool, bool]:
        """
        Check if document has been processed before.

        Args:
            doc_id: Document ID
            content_hash: Hash of document content for comparison

        Returns:
            (is_processed, has_changed) tuple
        """
        if doc_id not in self.state["processed_docs"]:
            return False, False

        old_hash = self.state["processed_docs"][doc_id]
        is_new = old_hash != content_hash

        return True, is_new

    def mark_processed(self, doc_id: str, content_hash: str, version: str):
        """Mark document as processed."""
        self.state["processed_docs"][doc_id] = content_hash

        if doc_id not in self.state["version_history"]:
            self.state["version_history"][doc_id] = []
        self.state["version_history"][doc_id].append({
            "version": version,
            "hash": content_hash,
            "processed_at": datetime.utcnow().isoformat() + "Z",
        })

    def increment_stats(self, new_count: int = 0, updated_count: int = 0):
        """Update statistics."""
        stats = self.state["stats"]
        stats["total_runs"] += 1
        stats["total_processed"] += new_count + updated_count
        stats["total_new"] += new_count
        stats["total_updated"] += updated_count

    def record_error(self, error: str):
        """Record last error."""
        self.state["stats"]["last_error"] = {
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def get_summary(self) -> dict:
        """Get state summary."""
        return {
            "last_run": self.state.get("last_run"),
            "total_documents": len(self.state["processed_docs"]),
            "stats": self.state["stats"],
        }


# ------------------------------------------------------------------------------
# Notification
# ------------------------------------------------------------------------------

class NotificationSender:
    """Send pipeline completion notifications."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize notification sender.

        Args:
            config_path: Path to notification config JSON
        """
        self.config = self._load_config(config_path)

    def _load_config(self, path: Optional[str]) -> dict:
        """Load notification config."""
        default_path = Path("config/notifications.json")

        if path:
            config_path = Path(path)
        elif default_path.exists():
            config_path = default_path
        else:
            return {}

        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("[WARN] Could not load notification config: %s", e)
            return {}

    def send_completion(
        self,
        new_docs: int,
        updated_docs: int,
        total_chunks: int,
        error: Optional[str] = None,
    ):
        """
        Send completion notification.

        Args:
            new_docs: Number of new documents indexed
            updated_docs: Number of updated documents
            total_chunks: Total chunks in database
            error: Error message if pipeline failed
        """
        if error:
            message = f"❌ Pipeline GAGAL: {error}"
            status = "FAILED"
        else:
            message = (
                f"✅ Pipeline selesai: "
                f"{new_docs} dokumen baru, "
                f"{updated_docs} diperbarui, "
                f"{total_chunks} total chunks"
            )
            status = "SUCCESS"

        logger.info("[NOTIFY] %s", message)

        # Console notification
        print(f"\n{'='*60}")
        print(f"[{status}] {message}")
        print(f"{'='*60}\n")

        # Email notification (if configured)
        if self.config.get("email"):
            self._send_email(message, status)

        # Webhook notification (if configured)
        if self.config.get("webhook_url"):
            self._send_webhook({
                "status": status,
                "message": message,
                "new_docs": new_docs,
                "updated_docs": updated_docs,
                "total_chunks": total_chunks,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

    def _send_email(self, message: str, status: str):
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText

            email_config = self.config["email"]
            smtp_host = email_config.get("smtp_host")
            smtp_port = email_config.get("smtp_port", 587)
            username = email_config.get("username")
            password = email_config.get("password")
            to_addr = email_config.get("to")

            if not all([smtp_host, username, password, to_addr]):
                logger.debug("[SKIP] Email not fully configured")
                return

            msg = MIMEText(message)
            msg["Subject"] = f"IndoGovRAG Pipeline {status}"
            msg["From"] = username
            msg["To"] = to_addr

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            logger.info("[EMAIL] Sent to %s", to_addr)

        except Exception as e:
            logger.warning("[WARN] Email failed: %s", e)

    def _send_webhook(self, payload: dict):
        """Send webhook notification."""
        try:
            import requests

            url = self.config["webhook_url"]
            timeout = self.config.get("webhook_timeout", 10)

            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()

            logger.info("[WEBHOOK] Sent to %s", url)

        except Exception as e:
            logger.warning("[WARN] Webhook failed: %s", e)


# ------------------------------------------------------------------------------
# Pipeline Scheduler
# ------------------------------------------------------------------------------

class PipelineScheduler:
    """
    Scheduled pipeline runner.

    Runs the full pipeline on a schedule (default: weekly).
    """

    def __init__(
        self,
        state_path: str = "data/pipeline/state.json",
        notification_config: Optional[str] = None,
        scrape_portals: Optional[list[str]] = None,
        max_docs_per_run: int = 100,
    ):
        """
        Initialize scheduler.

        Args:
            state_path: Path to state file
            notification_config: Path to notification config
            scrape_portals: List of portals to scrape (None = all)
            max_docs_per_run: Max documents to process per run
        """
        self.state = PipelineState(state_path)
        self.notifier = NotificationSender(notification_config)
        self.portals = scrape_portals
        self.max_docs = max_docs_per_run

        # Initialize pipeline components
        self.scraper = JDIHScraper(max_docs_per_portal=max_docs_per_run)
        self.chunker = PipelineChunker()
        self.embedder = PipelineEmbedder()

        # Scheduler
        self.scheduler = BackgroundScheduler()

        logger.info("[INIT] Pipeline scheduler ready")
        logger.info("  Portals: %s", scrape_portals or "all")
        logger.info("  Max docs: %d per run", max_docs_per_run)

    def run_once(self) -> dict:
        """
        Run the pipeline once immediately.

        Returns:
            Dict with run statistics
        """
        logger.info("[RUN] Starting pipeline run...")

        new_docs = 0
        updated_docs = 0
        error = None

        try:
            # Step 1: Scrape documents
            logger.info("[STEP 1/3] Scraping documents...")
            scraped_docs = self.scraper.scrape_all(portals=self.portals)
            logger.info("[OK] Scraped %d documents", len(scraped_docs))

            # Step 2: Process and chunk documents
            logger.info("[STEP 2/3] Processing and chunking...")
            for doc_meta in scraped_docs[:self.max_docs]:
                doc_id = doc_meta.get("doc_id") or doc_meta.get("nomor_regulasi")

                # Calculate content hash for change detection
                content_hash = self._calculate_hash(doc_meta)

                # Check if already processed
                is_processed, has_changed = self.state.is_processed(doc_id, content_hash)

                if is_processed and not has_changed:
                    logger.debug("[SKIP] %s already processed, no changes", doc_id)
                    continue

                # Check if this is an update (new version)
                if is_processed and has_changed:
                    # Get old version
                    old_version = self.state.state["version_history"].get(doc_id, [])[-1]["version"]
                    new_version = str(float(old_version) + 0.1)

                    # Mark old chunks as superseded
                    self.chunker.mark_superseded(doc_id, f"{doc_id}_v{new_version}")

                    updated_docs += 1
                    logger.info("[UPDATE] %s has changed, version %s -> %s",
                                doc_id, old_version, new_version)
                else:
                    new_version = "1.0"
                    new_docs += 1
                    logger.info("[NEW] Processing new document: %s", doc_id)

                # Process document (download PDF, extract, chunk)
                chunks = self.chunker.process_document(
                    metadata=doc_meta,
                    pdf_url=doc_meta.get("pdf_url"),
                    version=new_version,
                )

                # Mark as processed
                self.state.mark_processed(doc_id, content_hash, new_version)

                if len(chunks) == 0:
                    logger.warn("[WARN] No chunks generated for %s", doc_id)

            # Step 3: Rebuild BM25 index (only if we added new docs)
            if new_docs + updated_docs > 0:
                logger.info("[STEP 3/3] Rebuilding BM25 index...")
                self.embedder.rebuild_bm25_index()
                logger.info("[OK] BM25 index rebuilt")
            else:
                logger.info("[STEP 3/3] No new documents, skipping BM25 rebuild")

            # Update stats
            self.state.increment_stats(new_docs, updated_docs)
            self.state.save()

        except Exception as e:
            error = str(e)
            logger.exception("[ERR] Pipeline run failed")
            self.state.record_error(error)

        # Get total chunks
        stats = self.embedder.get_stats()
        total_chunks = stats.get("chromadb_chunks", 0)

        # Send notification
        self.notifier.send_completion(
            new_docs=new_docs,
            updated_docs=updated_docs,
            total_chunks=total_chunks,
            error=error,
        )

        return {
            "new_docs": new_docs,
            "updated_docs": updated_docs,
            "total_chunks": total_chunks,
            "error": error,
        }

    def start_weekly(self, day_of_week: str = "sun", hour: int = 2, minute: int = 0):
        """
        Start weekly scheduled runs.

        Args:
            day_of_week: Day of week (mon, tue, wed, thu, fri, sat, sun)
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        # Map day names to cron values
        day_map = {
            "mon": "mon",
            "tue": "tue",
            "wed": "wed",
            "thu": "thu",
            "fri": "fri",
            "sat": "sat",
            "sun": "sun",
        }

        cron_day = day_map.get(day_of_week.lower(), "sun")

        trigger = CronTrigger(
            day_of_week=cron_day,
            hour=hour,
            minute=minute,
        )

        self.scheduler.add_job(
            self.run_once,
            trigger=trigger,
            id="weekly_pipeline",
            name="Weekly Document Pipeline",
        )

        self.scheduler.start()

        logger.info(
            "[SCHED] Weekly pipeline scheduled: every %s at %02d:%02d",
            day_of_week.upper(), hour, minute
        )
        logger.info("[INFO] Press Ctrl+C to stop")

    def start_daily(self, hour: int = 3, minute: int = 0):
        """Start daily scheduled runs."""
        trigger = CronTrigger(hour=hour, minute=minute)

        self.scheduler.add_job(
            self.run_once,
            trigger=trigger,
            id="daily_pipeline",
            name="Daily Document Pipeline",
        )

        self.scheduler.start()

        logger.info("[SCHED] Daily pipeline scheduled: %02d:%02d", hour, minute)
        logger.info("[INFO] Press Ctrl+C to stop")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("[SCHED] Stopped")

    def _calculate_hash(self, doc_meta: dict) -> str:
        """Calculate hash of document metadata for change detection."""
        key_str = json.dumps(doc_meta, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Scheduler - Automated document processing")
    parser.add_argument("--action", choices=["run", "schedule-weekly", "schedule-daily"],
                        default="run", help="Action to perform")
    parser.add_argument("--day", default="sun",
                        help="Day of week for weekly schedule (mon-sun)")
    parser.add_argument("--hour", type=int, default=2,
                        help="Hour for scheduled run (0-23)")
    parser.add_argument("--minute", type=int, default=0,
                        help="Minute for scheduled run (0-59)")
    parser.add_argument("--max-docs", type=int, default=100,
                        help="Maximum documents per run")
    parser.add_argument("--portals", nargs="+",
                        choices=["kemenkumham", "peraturan_go_id", "all"],
                        help="Portals to scrape (default: all)")

    args = parser.parse_args()

    portals = None if not args.portals or "all" in args.portals else args.portals

    scheduler = PipelineScheduler(
        scrape_portals=portals,
        max_docs_per_run=args.max_docs,
    )

    try:
        if args.action == "run":
            # Run once and exit
            result = scheduler.run_once()

            print("\n[RESULT] Run complete")
            print(f"  New documents: {result['new_docs']}")
            print(f"  Updated documents: {result['updated_docs']}")
            print(f"  Total chunks: {result['total_chunks']}")

            if result['error']:
                print(f"  Error: {result['error']}")
                exit(1)

        elif args.action == "schedule-weekly":
            scheduler.start_weekly(day_of_week=args.day, hour=args.hour, minute=args.minute)

            # Keep script running
            import time
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                scheduler.stop()

        elif args.action == "schedule-daily":
            scheduler.start_daily(hour=args.hour, minute=args.minute)

            import time
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                scheduler.stop()

    except Exception as e:
        logger.exception("[FATAL] Scheduler failed")
        exit(1)