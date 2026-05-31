#!/usr/bin/env python3
"""
IndoGovRAG Pipeline - Main Entry Point

Runs the complete document processing pipeline:
  1. Scrape legal documents from JDIH portals
  2. Download PDFs and extract text
  3. Chunk documents into segments
  4. Generate embeddings and build BM25 index
  5. Store in ChromaDB for RAG retrieval

Usage:
  python -m pipeline.run --help
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.jdih_scraper import JDIHScraper
from pipeline.chunker import PipelineChunker
from pipeline.embedder import PipelineEmbedder
from pipeline.scheduler import PipelineScheduler
from pipeline.versioning import VersionManager

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
# Main Pipeline Runner
# ------------------------------------------------------------------------------

class PipelineRunner:
    """
    Main pipeline orchestrator.

    Coordinates the full workflow from scraping to indexing.
    """

    def __init__(
        self,
        portals: Optional[list[str]] = None,
        max_docs: int = 50,
        chunk_size: int = 512,
        overlap: int = 50,
        batch_size: int = 32,
    ):
        """
        Initialize pipeline runner.

        Args:
            portals: List of portals to scrape (None = all)
            max_docs: Maximum documents per portal
            chunk_size: Target chunk size in tokens
            overlap: Token overlap between chunks
            batch_size: Embedding batch size
        """
        self.portals = portals
        self.max_docs = max_docs
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.batch_size = batch_size

        # Initialize components
        self.scraper = JDIHScraper(max_docs_per_portal=max_docs)
        self.chunker = PipelineChunker(
            chunk_size=chunk_size,
            overlap=overlap,
        )
        self.embedder = PipelineEmbedder(batch_size=batch_size)
        self.version_manager = VersionManager()

        logger.info("[INIT] Pipeline runner ready")
        logger.info("  Portals: %s", portals or "all")
        logger.info("  Max docs: %d per portal", max_docs)

    def run(self, rebuild_bm25: bool = True) -> dict:
        """
        Run the full pipeline.

        Args:
            rebuild_bm25: Rebuild BM25 index after processing

        Returns:
            Dict with pipeline statistics
        """
        logger.info("="*60)
        logger.info("[START] Running IndoGovRAG Pipeline")
        logger.info("="*60)

        stats = {
            "scraped": 0,
            "processed": 0,
            "new": 0,
            "updated": 0,
            "chunks": 0,
            "errors": [],
        }

        try:
            # Step 1: Scrape documents
            logger.info("\n[STEP 1/3] Scraping documents from portals...")
            scraped_docs = self.scraper.scrape_all(portals=self.portals)
            stats["scraped"] = len(scraped_docs)
            logger.info("[OK] Scraped %d documents", len(scraped_docs))

            # Step 2: Process and chunk documents
            logger.info("\n[STEP 2/3] Processing and chunking documents...")

            for doc_meta in scraped_docs:
                doc_id = doc_meta.get("doc_id") or doc_meta.get("nomor_regulasi")

                try:
                    # Calculate content hash for versioning
                    import hashlib
                    content_hash = hashlib.sha256(
                        json.dumps(doc_meta, sort_keys=True).encode()
                    ).hexdigest()[:16]

                    # Register document version
                    version, is_new = self.version_manager.register_document(
                        doc_id, content_hash
                    )

                    if is_new:
                        stats["new"] += 1
                        logger.info("[NEW] Processing new document: %s (v%s)", doc_id, version)
                    else:
                        stats["updated"] += 1
                        logger.info("[UPDATE] Processing updated document: %s (v%s)", doc_id, version)
                        # Mark old chunks as superseded
                        self.chunker.mark_superseded(doc_id, f"{doc_id}_v{version}")

                    # Process document
                    chunks = self.chunker.process_document(
                        metadata=doc_meta,
                        pdf_url=doc_meta.get("pdf_url"),
                        version=version,
                    )

                    if chunks:
                        stats["processed"] += 1
                        stats["chunks"] += len(chunks)
                        logger.debug("[OK] %s: %d chunks", doc_id, len(chunks))
                    else:
                        logger.warn("[WARN] No chunks for %s", doc_id)

                except Exception as e:
                    error_msg = f"{doc_id}: {str(e)}"
                    stats["errors"].append(error_msg)
                    logger.error("[ERR] Failed to process %s: %s", doc_id, e)

            logger.info("[OK] Processed %d documents, %d chunks total",
                        stats["processed"], stats["chunks"])

            # Step 3: Rebuild BM25 index
            if rebuild_bm25 and stats["processed"] > 0:
                logger.info("\n[STEP 3/3] Rebuilding BM25 index...")
                self.embedder.rebuild_bm25_index()
                logger.info("[OK] BM25 index rebuilt")
            else:
                logger.info("\n[STEP 3/3] Skipping BM25 rebuild (no new documents)")

        except Exception as e:
            logger.exception("[FATAL] Pipeline failed")
            stats["errors"].append(str(e))

        # Final statistics
        self._print_final_stats(stats)

        return stats

    def _print_final_stats(self, stats: dict):
        """Print final statistics."""
        logger.info("\n" + "="*60)
        logger.info("[COMPLETE] Pipeline Run Summary")
        logger.info("="*60)

        logger.info("  Documents scraped: %d", stats["scraped"])
        logger.info("  Documents processed: %d", stats["processed"])
        logger.info("  New documents: %d", stats["new"])
        logger.info("  Updated documents: %d", stats["updated"])
        logger.info("  Total chunks: %d", stats["chunks"])

        if stats["errors"]:
            logger.warn("  Errors: %d", len(stats["errors"]))
            for err in stats["errors"][:3]:
                logger.warn("    - %s", err[:100])

        # ChromaDB stats
        chroma_stats = self.embedder.get_stats()
        logger.info("\n  ChromaDB Stats:")
        logger.info("    Total chunks: %d", chroma_stats.get("chromadb_chunks", 0))
        logger.info("    BM25 docs: %d", chroma_stats.get("bm25_docs", 0))

        # Version manager stats
        version_stats = self.version_manager.get_stats()
        logger.info("\n  Version Stats:")
        logger.info("    Total tracked: %d", version_stats.get("total_documents", 0))
        logger.info("    Active: %d", version_stats.get("active_documents", 0))
        logger.info("    Superseded: %d", version_stats.get("superseded_documents", 0))

        logger.info("="*60)


# ------------------------------------------------------------------------------
# CLI Entry Point
# ------------------------------------------------------------------------------

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="IndoGovRAG Pipeline - Document Processing for Indonesian Government Legal Documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline on all portals (max 50 docs each)
  python -m pipeline.run

  # Run on specific portal
  python -m pipeline.run --portals kemenkumham --max-docs 100

  # Start weekly scheduler
  python -m pipeline.run --schedule weekly --day sun --hour 2

  # Run once and show stats only
  python -m pipeline.run --stats-only
        """
    )

    # Pipeline options
    parser.add_argument(
        "--portals",
        nargs="+",
        choices=["kemenkumham", "peraturan_go_id", "all"],
        help="Portals to scrape (default: all)"
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=50,
        help="Maximum documents per portal (default: 50)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Target chunk size in tokens (default: 512)"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Token overlap between chunks (default: 50)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size (default: 32)"
    )
    parser.add_argument(
        "--no-bm25-rebuild",
        action="store_true",
        help="Skip BM25 index rebuild"
    )

    # Scheduler options
    parser.add_argument(
        "--schedule",
        choices=["weekly", "daily", "once"],
        default="once",
        help="Run mode (default: once)"
    )
    parser.add_argument(
        "--day",
        default="sun",
        choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        help="Day of week for weekly schedule (default: sun)"
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=2,
        help="Hour for scheduled run (0-23, default: 2)"
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="Minute for scheduled run (0-59, default: 0)"
    )

    # Utility options
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Show current stats and exit"
    )
    parser.add_argument(
        "--search",
        help="Test search query (requires embedder)"
    )

    args = parser.parse_args()

    # Handle stats-only
    if args.stats_only:
        embedder = PipelineEmbedder()
        stats = embedder.get_stats()
        vm = VersionManager()

        print("\n[STAT] Current Pipeline State")
        print("=" * 50)
        print("\nChromaDB:")
        print(f"  Total chunks: {stats.get('chromadb_chunks', 0)}")
        print(f"  BM25 docs: {stats.get('bm25_docs', 0)}")
        print(f"  BM25 vocab: {stats.get('bm25_vocab_size', 0)}")

        v_stats = vm.get_stats()
        print("\nVersioning:")
        print(f"  Total tracked: {v_stats.get('total_documents', 0)}")
        print(f"  Active: {v_stats.get('active_documents', 0)}")
        print(f"  Superseded: {v_stats.get('superseded_documents', 0)}")
        return

    # Handle search test
    if args.search:
        embedder = PipelineEmbedder()
        results = embedder.search_hybrid(args.search, n_results=10, alpha=0.7)

        print(f"\n[SEARCH] Query: {args.search}")
        print(f"Results: {len(results)}")
        print("=" * 50)

        for i, r in enumerate(results, 1):
            print(f"\n{i}. Score: {r.get('fused_score', r.get('score', 0)):.3f}")
            print(f"   Doc: {r['metadata'].get('doc_id', 'N/A')}")
            print(f"   Type: {r['metadata'].get('category', 'N/A')}")
            print(f"   Text: {r['text'][:150]}...")
            if r.get('superseded_warning'):
                print(f"   ⚠️  {r['superseded_warning']}")
        return

    # Handle scheduler mode
    if args.schedule != "once":
        scheduler = PipelineScheduler(
            scrape_portals=None if not args.portals or "all" in args.portals else args.portals,
            max_docs_per_run=args.max_docs,
        )

        if args.schedule == "weekly":
            scheduler.start_weekly(day_of_week=args.day, hour=args.hour, minute=args.minute)
        elif args.schedule == "daily":
            scheduler.start_daily(hour=args.hour, minute=args.minute)

        # Keep running
        import time
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            scheduler.stop()
        return

    # Run pipeline once
    portals = None if not args.portals or "all" in args.portals else args.portals

    runner = PipelineRunner(
        portals=portals,
        max_docs=args.max_docs,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        batch_size=args.batch_size,
    )

    stats = runner.run(rebuild_bm25=not args.no_bm25_rebuild)

    # Exit with error code if there were errors
    if stats["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()