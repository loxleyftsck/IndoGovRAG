"""
Pipeline Chunker - Download PDFs, Extract Text, and Chunk for RAG

Features:
  - Downloads PDFs from URLs (or uses local files)
  - Extracts text using pdfplumber
  - Chunks into 512-token segments with 50-token overlap
  - Preserves metadata: document_id, halaman, bab, pasal (if detectable)
  - Stores chunks in ChromaDB collection
  - Handles document versioning (superseded docs)

Requirements:
  - pdfplumber (in requirements.txt)
  - ChromaDB (already in use)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber
import requests
from tqdm import tqdm

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
# Data Classes
# ------------------------------------------------------------------------------

@dataclass
class Chunk:
    """
    A document chunk with full metadata.

    Attributes:
        chunk_id: Unique chunk identifier (doc_hash + sequence)
        text: Chunk text content
        doc_id: Document ID (from scraper)
        doc_version: Document version string
        seq: Chunk sequence number (0-indexed)
        start_char: Character offset in original document
        end_char: Character offset end
        page_num: PDF page number (0-indexed)
        tokens: Approximate token count
        metadata: Additional metadata
        is_superseded: Whether this chunk is from a superseded document
        superseded_by: Doc ID of newer version (if superseded)
    """
    chunk_id: str
    text: str
    doc_id: str
    doc_version: str
    seq: int
    start_char: int
    end_char: int
    page_num: int
    tokens: int
    metadata: dict[str, Any] = field(default_factory=dict)
    is_superseded: bool = False
    superseded_by: str | None = None

    @property
    def storage_id(self) -> str:
        """ID used for storage in ChromaDB."""
        return f"{self.doc_id}_v{self.doc_version}_chunk{self.seq:04d}"

    def to_dict(self) -> dict:
        """Convert to dictionary for ChromaDB storage."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "doc_id": self.doc_id,
            "doc_version": self.doc_version,
            "seq": self.seq,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "page_num": self.page_num,
            "tokens": self.tokens,
            "metadata": self.metadata,
            "is_superseded": self.is_superseded,
            "superseded_by": self.superseded_by,
        }


# ------------------------------------------------------------------------------
# PDF Text Extraction
# ------------------------------------------------------------------------------

class PDFTextExtractor:
    """Extract text from PDFs with page and section detection."""

    # Indonesian document structure patterns
    SECTION_PATTERNS = {
        "bab": re.compile(r"^BAB\s+[IVXLCM\d]+", re.MULTILINE),
        "pasal": re.compile(r"^Pasal\s+\d+", re.MULTILINE),
        "bagian": re.compile(r"^Bagian\s+[A-Z\d]+", re.MULTILINE),
        "paragraf": re.compile(r"^Paragraf\s+\d+", re.MULTILINE),
        "ayat": re.compile(r"^\(\d+\)", re.MULTILINE),
        "huruf": re.compile(r"^[a-z]\)", re.MULTILINE),
        "angka": re.compile(r"^\d+\.", re.MULTILINE),
    }

    def __init__(
        self,
        download_dir: str = "data/pipeline/pdfs",
        cache_dir: str = "data/pipeline/pdf_cache",
    ):
        """
        Initialize PDF text extractor.

        Args:
            download_dir: Directory to save downloaded PDFs
            cache_dir: Directory to cache extracted text
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; IndoGovRAG/1.0)",
        })

    def extract_from_url(self, url: str, doc_id: str) -> str | None:
        """
        Download PDF from URL and extract text.

        Args:
            url: PDF URL
            doc_id: Document ID for caching

        Returns:
            Extracted text or None if failed
        """
        # Check cache first
        cache_path = self.cache_dir / f"{doc_id}.txt"
        if cache_path.exists():
            logger.debug("[CACHE] Using cached text for %s", doc_id)
            return cache_path.read_text(encoding="utf-8")

        # Download PDF
        pdf_path = self._download_pdf(url, doc_id)
        if not pdf_path:
            return None

        # Extract text
        text = self._extract_from_file(pdf_path, doc_id)
        if text:
            # Cache the extracted text
            cache_path.write_text(text, encoding="utf-8")

        return text

    def extract_from_file(self, pdf_path: str | Path, doc_id: str) -> str | None:
        """
        Extract text from local PDF file.

        Args:
            pdf_path: Path to PDF file
            doc_id: Document ID for caching

        Returns:
            Extracted text or None if failed
        """
        cache_path = self.cache_dir / f"{doc_id}.txt"
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")

        text = self._extract_from_file(pdf_path, doc_id)
        if text:
            cache_path.write_text(text, encoding="utf-8")
        return text

    def _download_pdf(self, url: str, doc_id: str) -> Path | None:
        """Download PDF from URL."""
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in doc_id)
        pdf_path = self.download_dir / f"{safe_name}.pdf"

        if pdf_path.exists():
            logger.debug("[EXISTS] PDF already cached: %s", pdf_path.name)
            return pdf_path

        try:
            logger.info("[DOWNLOAD] %s → %s", url[:80], pdf_path.name)
            resp = self.session.get(url, timeout=60, stream=True)
            resp.raise_for_status()

            with open(pdf_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info("[OK] Downloaded %s (%.1f KB)", pdf_path.name, pdf_path.stat().st_size / 1024)
            return pdf_path

        except Exception as e:
            logger.error("[ERR] Failed to download %s: %s", url[:60], e)
            return None

    def _extract_from_file(self, pdf_path: str | Path, doc_id: str) -> str | None:
        """Extract text from PDF file using pdfplumber."""
        try:
            full_text = []

            with pdfplumber.open(pdf_path) as pdf:
                logger.debug("[PDF] Processing %d pages", len(pdf.pages))

                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            # Clean up text
                            text = self._clean_text(text)
                            # Add page marker for reference
                            full_text.append(f"[PAGE {page_num + 1}]\n{text}")

                    except Exception as e:
                        logger.debug("[WARN] Page %d failed: %s", page_num, e)
                        continue

            if not full_text:
                logger.warn("[WARN] No text extracted from %s", pdf_path)
                return None

            text = "\n\n".join(full_text)

            if len(text) < 100:
                logger.warn("[WARN] Text too short from %s: %d chars", pdf_path, len(text))
                return None

            logger.info("[OK] Extracted %d chars from %s", len(text), pdf_path.name)
            return text

        except Exception as e:
            logger.error("[ERR] pdfplumber failed on %s: %s", pdf_path, e)
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Fix common PDF extraction issues
        text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse excessive newlines
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)  # Remove control chars
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        text = text.strip()

        return text

    def detect_sections(self, text: str) -> dict[str, list[tuple[int, int]]]:
        """
        Detect document sections (BAB, Pasal, etc.) with their positions.

        Returns:
            Dict mapping section type to list of (start, end) char positions
        """
        sections = {}

        for section_type, pattern in self.SECTION_PATTERNS.items():
            matches = []
            for match in pattern.finditer(text):
                matches.append((match.start(), match.end()))
            if matches:
                sections[section_type] = matches

        return sections


# ------------------------------------------------------------------------------
# Document Chunker
# ------------------------------------------------------------------------------

class PipelineChunker:
    """
    Chunk documents for RAG pipeline.

    Chunks PDF documents into 512-token segments with 50-token overlap.
    Preserves structural metadata (page, bab, pasal) for retrieval.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        min_chunk_size: int = 100,
        persist_dir: str = "data/vector_db/chroma",
        collection_name: str = "indonesian_gov_docs",
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Token overlap between chunks
            min_chunk_size: Minimum chunk size in tokens
            persist_dir: ChromaDB persist directory
            collection_name: ChromaDB collection name
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        import chromadb
        from chromadb.config import Settings

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Text extractor
        self.extractor = PDFTextExtractor()

        logger.info("[INIT] Chunker: chunk=%d overlap=%d collection=%s",
                    chunk_size, overlap, collection_name)

    def process_document(
        self,
        metadata: dict,
        pdf_url: str | None = None,
        pdf_path: str | None = None,
        version: str = "1.0",
        is_superseded: bool = False,
        superseded_by: str | None = None,
    ) -> list[Chunk]:
        """
        Process a single document: download, extract, chunk, store.

        Args:
            metadata: Document metadata (from scraper)
            pdf_url: URL to download PDF
            pdf_path: Local path to PDF (alternative to url)
            version: Document version
            is_superseded: Whether this doc is superseded
            superseded_by: Newer doc ID (if superseded)

        Returns:
            List of created chunks
        """
        doc_id = metadata.get("doc_id") or metadata.get("nomor_regulasi")

        if not doc_id:
            raise ValueError("Document metadata must include 'doc_id' or 'nomor_regulasi'")

        # Extract text
        if pdf_url:
            text = self.extractor.extract_from_url(pdf_url, doc_id)
        elif pdf_path:
            text = self.extractor.extract_from_file(pdf_path, doc_id)
        else:
            logger.error("[ERR] No PDF source for %s", doc_id)
            return []

        if not text:
            logger.error("[ERR] Text extraction failed for %s", doc_id)
            return []

        # Detect sections
        sections = self.extractor.detect_sections(text)

        # Chunk
        chunks = self._chunk_text(
            text=text,
            doc_id=doc_id,
            version=version,
            metadata=metadata,
            sections=sections,
            is_superseded=is_superseded,
            superseded_by=superseded_by,
        )

        # Store in ChromaDB
        self._store_chunks(chunks)

        logger.info("[OK] %s: %d chunks, %d tokens total",
                    doc_id, len(chunks), sum(c.tokens for c in chunks))

        return chunks

    def process_batch(
        self,
        documents: list[dict],
        show_progress: bool = True,
    ) -> dict[str, list[Chunk]]:
        """
        Process multiple documents in batch.

        Args:
            documents: List of document metadata dicts
            show_progress: Show progress bar

        Returns:
            Dict mapping doc_id to list of chunks
        """
        results = {}
        iterator = tqdm(documents, desc="Processing documents") if show_progress else documents

        for doc_meta in iterator:
            doc_id = doc_meta.get("doc_id") or doc_meta.get("nomor_regulasi")

            try:
                chunks = self.process_document(
                    metadata=doc_meta,
                    pdf_url=doc_meta.get("pdf_url"),
                    version=doc_meta.get("version", "1.0"),
                )

                if chunks:
                    results[doc_id] = chunks

            except Exception as e:
                logger.error("[ERR] Failed to process %s: %s", doc_id, e)

        return results

    def _chunk_text(
        self,
        text: str,
        doc_id: str,
        version: str,
        metadata: dict,
        sections: dict,
        is_superseded: bool = False,
        superseded_by: str | None = None,
    ) -> list[Chunk]:
        """
        Chunk text into segments.

        Strategy:
        1. Split on section boundaries (BAB, Pasal, etc.) first
        2. If sections too large, split on paragraphs
        3. If paragraphs too large, split on sentences
        4. Apply overlap between chunks
        """
        chunks = []

        # Get section boundaries
        all_boundaries = []
        for section_type, matches in sections.items():
            for start, end in matches:
                all_boundaries.append((start, section_type, text[start:end].strip()))

        # Sort by position
        all_boundaries.sort(key=lambda x: x[0])

        # Add start and end boundaries
        boundaries = [(0, "start", text[:0])] + all_boundaries + [(len(text), "end", "")]
        boundaries = [(b[0], b[1]) for b in boundaries]

        # Create segments based on boundaries
        segments = []
        for i in range(len(boundaries) - 1):
            start_pos, section_type = boundaries[i]
            end_pos, _ = boundaries[i + 1]
            segment_text = text[start_pos:end_pos].strip()

            if len(segment_text) > 20:  # Skip very short segments
                segments.append({
                    "text": segment_text,
                    "start": start_pos,
                    "section": section_type,
                })

        # Now create chunks from segments
        current_chunk_text = ""
        current_chunk_start = 0
        current_chunk_section = "start"
        current_char_pos = 0
        seq = 0

        for segment in segments:
            segment_text = segment["text"]
            segment_start = segment["start"]
            segment_section = segment["section"]
            segment_tokens = self._count_tokens(segment_text)

            # Check if adding this segment would exceed chunk size
            current_tokens = self._count_tokens(current_chunk_text)

            if current_tokens + segment_tokens <= self.chunk_size:
                # Add to current chunk
                if not current_chunk_text:
                    current_chunk_start = segment_start
                    current_chunk_section = segment_section
                current_chunk_text += ("\n\n" if current_chunk_text else "") + segment_text
            else:
                # Finalize current chunk if it exists
                if current_chunk_text:
                    chunks.append(self._create_chunk(
                        text=current_chunk_text,
                        doc_id=doc_id,
                        version=version,
                        seq=seq,
                        start_char=current_chunk_start,
                        end_char=current_char_pos,
                        section=current_chunk_section,
                        metadata=metadata,
                        is_superseded=is_superseded,
                        superseded_by=superseded_by,
                    ))
                    seq += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk_text)
                current_chunk_text = overlap_text + "\n\n" + segment_text if overlap_text else segment_text
                current_chunk_start = segment_start - len(overlap_text) if overlap_text else segment_start
                current_chunk_section = segment_section

            current_char_pos = segment_start + len(segment_text)

        # Add final chunk
        if current_chunk_text and self._count_tokens(current_chunk_text) >= self.min_chunk_size:
            chunks.append(self._create_chunk(
                text=current_chunk_text,
                doc_id=doc_id,
                version=version,
                seq=seq,
                start_char=current_chunk_start,
                end_char=len(text),
                section=current_chunk_section,
                metadata=metadata,
                is_superseded=is_superseded,
                superseded_by=superseded_by,
            ))

        return chunks

    def _create_chunk(
        self,
        text: str,
        doc_id: str,
        version: str,
        seq: int,
        start_char: int,
        end_char: int,
        section: str,
        metadata: dict,
        is_superseded: bool,
        superseded_by: str | None,
    ) -> Chunk:
        """Create a Chunk object with metadata."""
        chunk_id = hashlib.sha256(
            f"{doc_id}_{version}_{seq}_{text[:50]}".encode()
        ).hexdigest()[:16]

        chunk_metadata = {
            **metadata,
            "section_type": section,
            "chunked_at": datetime.utcnow().isoformat() + "Z",
        }

        return Chunk(
            chunk_id=chunk_id,
            text=text,
            doc_id=doc_id,
            doc_version=version,
            seq=seq,
            start_char=start_char,
            end_char=end_char,
            page_num=0,  # Could be enhanced to track page
            tokens=self._count_tokens(text),
            metadata=chunk_metadata,
            is_superseded=is_superseded,
            superseded_by=superseded_by,
        )

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from previous chunk."""
        if not text:
            return ""

        words = text.split()
        overlap_words = words[-self.overlap:] if len(words) > self.overlap else words
        return " ".join(overlap_words)

    def _count_tokens(self, text: str) -> int:
        """Approximate token count for Indonesian text."""
        # Rough approximation: ~1.3 words per token for Indonesian
        word_count = len(text.split())
        return max(1, int(word_count / 1.3))

    def _store_chunks(self, chunks: list[Chunk]):
        """Store chunks in ChromaDB."""
        if not chunks:
            return

        ids = [c.storage_id for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [c.to_dict() for c in chunks]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

    def mark_superseded(self, old_doc_id: str, new_doc_id: str):
        """
        Mark all chunks of old_doc_id as superseded by new_doc_id.

        Args:
            old_doc_id: Old document ID
            new_doc_id: Newer document ID
        """
        # Get all chunks for old document
        results = self.collection.get(
            where={"doc_id": old_doc_id},
        )

        if not results["ids"]:
            logger.warn("[WARN] No chunks found for %s", old_doc_id)
            return

        # Update metadata to mark as superseded
        updated_ids = []
        updated_metadata = []

        for i, chunk_id in enumerate(results["ids"]):
            current_meta = results["metadatas"][i] or {}
            updated_meta = {
                **current_meta,
                "is_superseded": True,
                "superseded_by": new_doc_id,
            }
            updated_ids.append(chunk_id)
            updated_metadata.append(updated_meta)

        # Update in ChromaDB
        if updated_ids:
            self.collection.update(
                ids=updated_ids,
                metadatas=updated_metadata,
            )
            logger.info("[OK] Marked %d chunks of %s as superseded by %s",
                        len(updated_ids), old_doc_id, new_doc_id)

    def get_stats(self) -> dict:
        """Get chunking statistics."""
        total_chunks = self.collection.count()

        # Get sample to analyze
        sample = self.collection.peek(limit=min(1000, total_chunks))

        stats = {
            "total_chunks": total_chunks,
            "collection_name": self.collection.name,
        }

        if sample["metadatas"]:
            superseded = sum(1 for m in sample["metadatas"] if m.get("is_superseded"))
            stats["superseded_ratio"] = superseded / len(sample["metadatas"])

            # Average tokens per chunk
            tokens = [m.get("tokens", 0) for m in sample["metadatas"]]
            stats["avg_tokens_per_chunk"] = sum(tokens) / len(tokens) if tokens else 0

        return stats


# =============================================================================
# CLI / Demo
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Chunker - Process and chunk PDF documents")
    parser.add_argument("--input", required=True,
                        help="Path to scraper registry JSON or directory")
    parser.add_argument("--collection", default="indonesian_gov_docs",
                        help="ChromaDB collection name")
    parser.add_argument("--chunk-size", type=int, default=512,
                        help="Target chunk size in tokens")
    parser.add_argument("--overlap", type=int, default=50,
                        help="Token overlap between chunks")

    args = parser.parse_args()

    chunker = PipelineChunker(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        collection_name=args.collection,
    )

    # Load documents from registry
    input_path = Path(args.input)

    if input_path.is_file():
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
        documents = data.get("documents", [])
    elif input_path.is_dir():
        # Load all JSON files in directory
        documents = []
        for json_file in input_path.glob("*.json"):
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            documents.extend(data.get("documents", []))
    else:
        print(f"[ERR] Invalid input path: {input_path}")
        exit(1)

    print(f"[INFO] Loaded {len(documents)} documents from {args.input}")

    # Process documents
    results = chunker.process_batch(documents, show_progress=True)

    print(f"\n[OK] Processed {len(results)} documents")
    print(f"     Total chunks created: {sum(len(chunks) for chunks in results.values())}")

    stats = chunker.get_stats()
    print(f"\n[STAT] Collection stats:")
    for k, v in stats.items():
        print(f"       {k}: {v}")