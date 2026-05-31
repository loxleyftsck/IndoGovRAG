"""
Pipeline Embedder - Generate Embeddings and Build BM25 Index

Features:
  - Embed chunks using sentence-transformers/paraphrase-multilingual-MPNet-base-v2
  - Build BM25 index for hybrid lexical search
  - Supports incremental re-embedding (new docs only)
  - ChromaDB integration (already embedded chunks stored directly)

Requirements:
  - sentence-transformers (in requirements.txt)
  - rank-bm25 (in requirements.txt)
  - chromadb (in requirements.txt)
"""

from __future__ import annotations

import json
import logging
import pickle
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# BM25 Index Builder
# ------------------------------------------------------------------------------

class BM25IndexBuilder:
    """
    BM25 index builder for lexical search.

    Stores index to disk for persistence and fast reload.
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        average_doc_length: Optional[int] = None,
    ):
        """
        Initialize BM25 builder.

        Args:
            k1: BM25 term frequency saturation parameter
            b: BM25 document length normalization parameter
            average_doc_length: Pre-set average document length
        """
        self.k1 = k1
        self.b = b
        self.avg_doc_len = average_doc_length

        self.doc_count = 0
        self.doc_lengths: list[int] = []
        self.doc_freqs: dict[str, int] = {}  # term -> num docs containing term
        self.doc_term_freqs: list[dict[str, int]] = []  # per-doc term frequencies
        self.vocab: dict[str, int] = {}  # term -> index

        self._built = False

    def build(self, documents: list[dict]):
        """
        Build BM25 index from documents.

        Args:
            documents: List of dicts with 'text' (required), 'doc_id' (optional)
        """
        if not documents:
            return

        import re
        from collections import Counter

        logger.info("[BUILD] Building BM25 index for %d documents", len(documents))

        self.doc_count = len(documents)
        self.doc_lengths = []
        self.doc_term_freqs = []
        term_to_idx: dict[str, int] = {}
        next_idx = 0

        for doc in documents:
            text = doc.get("text", "")
            tokens = self._tokenize(text)

            self.doc_lengths.append(sum(tf for tf in tokens.values()))

            doc_tf: dict[str, int] = {}
            for term, freq in tokens.items():
                doc_tf[term] = freq

                if term not in term_to_idx:
                    term_to_idx[term] = next_idx
                    next_idx += 1

                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

            self.doc_term_freqs.append(doc_tf)

        self.vocab = term_to_idx
        self.avg_doc_len = sum(self.doc_lengths) / self.doc_count if self.doc_count else 1
        self._built = True

        logger.info("[OK] BM25 index built: %d docs, %d vocab size, avg_len=%.1f",
                    self.doc_count, len(self.vocab), self.avg_doc_len)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Search BM25 index.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of (doc_index, score) tuples sorted by score descending
        """
        if not self._built:
            return []

        import re

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = np.zeros(self.doc_count)

        for term, q_tf in query_tokens.items():
            if term not in self.doc_freqs:
                continue

            df = self.doc_freqs[term]
            idf = np.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

            for doc_idx in range(self.doc_count):
                tf = self.doc_term_freqs[doc_idx].get(term, 0)
                doc_len = self.doc_lengths[doc_idx]

                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                score = idf * numerator / denominator

                scores[doc_idx] += score

        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((str(idx), float(scores[idx])))

        return results

    def _tokenize(self, text: str) -> dict[str, int]:
        """Tokenize text into word frequencies."""
        import re
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        words = [w for w in text.split() if len(w) > 2]
        from collections import Counter
        return dict(Counter(words))

    def save(self, path: Path | str):
        """Save index to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "k1": self.k1,
            "b": self.b,
            "avg_doc_len": self.avg_doc_len,
            "doc_count": self.doc_count,
            "doc_lengths": self.doc_lengths,
            "doc_freqs": self.doc_freqs,
            "doc_term_freqs": self.doc_term_freqs,
            "vocab": self.vocab,
        }

        with open(path, "wb") as f:
            pickle.dump(state, f)

        logger.info("[SAVE] BM25 index saved → %s", path)

    @classmethod
    def load(cls, path: Path | str) -> "BM25IndexBuilder":
        """Load index from disk."""
        path = Path(path)

        with open(path, "rb") as f:
            state = pickle.load(f)

        builder = cls(k1=state["k1"], b=state["b"])
        builder.avg_doc_len = state["avg_doc_len"]
        builder.doc_count = state["doc_count"]
        builder.doc_lengths = state["doc_lengths"]
        builder.doc_freqs = state["doc_freqs"]
        builder.doc_term_freqs = state["doc_term_freqs"]
        builder.vocab = state["vocab"]
        builder._built = True

        logger.info("[LOAD] BM25 index loaded from %s", path)
        return builder

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "doc_count": self.doc_count,
            "vocab_size": len(self.vocab),
            "avg_doc_length": self.avg_doc_len,
            "total_terms_indexed": sum(self.doc_lengths),
        }


# ------------------------------------------------------------------------------
# Pipeline Embedder
# ------------------------------------------------------------------------------

class PipelineEmbedder:
    """
    Embed document chunks and manage hybrid search index.

    Uses paraphrase-multilingual-MPNet-base-v2 for embeddings.
    Maintains BM25 index for lexical search.

    ChromaDB is used directly for semantic search (embeddings generated on insert).
    BM25 is used for keyword matching.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MPNet-base-v2",
        persist_dir: str = "data/vector_db/chroma",
        collection_name: str = "indonesian_gov_docs",
        bm25_index_path: str = "data/vector_db/bm25_index.pkl",
        batch_size: int = 32,
    ):
        """
        Initialize embedder.

        Args:
            model_name: HuggingFace model name for embeddings
            persist_dir: ChromaDB persist directory
            collection_name: ChromaDB collection name
            bm25_index_path: Path to save BM25 index
            batch_size: Batch size for embedding generation
        """
        self.model_name = model_name
        self.persist_dir = Path(persist_dir)
        self.bm25_index_path = Path(bm25_index_path)
        self.batch_size = batch_size

        # Initialize ChromaDB client
        import chromadb
        from chromadb.config import Settings

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Load embedding function
        self.embedding_fn = self._load_embedding_function(model_name)

        # Load or build BM25 index
        self.bm25 = self._load_or_build_bm25()

        logger.info("[INIT] Embedder ready")
        logger.info("  Model: %s", model_name)
        logger.info("  Collection: %s (%d chunks)", collection_name, self.collection.count())

    def _load_embedding_function(self, model_name: str):
        """Load sentence-transformers embedding function for ChromaDB."""
        from chromadb.utils import embedding_functions

        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name,
            device="cpu",  # Set "cuda" if GPU available
        )

    def _load_or_build_bm25(self) -> BM25IndexBuilder:
        """Load existing BM25 index or build new one."""
        if self.bm25_index_path.exists():
            try:
                return BM25IndexBuilder.load(self.bm25_index_path)
            except Exception as e:
                logger.warning("[WARN] Could not load BM25 index: %s. Rebuilding.", e)

        # Build new index from existing collection
        return self._build_bm25_from_collection()

    def _build_bm25_from_collection(self) -> BM25IndexBuilder:
        """Build BM25 index from existing ChromaDB collection."""
        logger.info("[BUILD] Building BM25 index from collection...")

        bm25 = BM25IndexBuilder()

        # Get all documents from collection (batch for large collections)
        all_docs = []
        batch_size = 1000
        offset = 0

        while True:
            batch = self.collection.get(
                limit=batch_size,
                offset=offset,
                include=["documents", "metadatas"]
            )

            if not batch["ids"]:
                break

            for i, doc_text in enumerate(batch["documents"]):
                meta = batch["metadatas"][i] or {}
                all_docs.append({
                    "text": doc_text,
                    "doc_id": meta.get("doc_id", batch["ids"][i]),
                    "metadata": meta,
                })

            offset += batch_size

        if all_docs:
            bm25.build(all_docs)
            bm25.save(self.bm25_index_path)
        else:
            logger.info("[BUILD] No documents in collection, empty BM25 index created")

        return bm25

    def add_chunks(self, chunks: list[dict], rebuild_bm25: bool = False):
        """
        Add chunks to ChromaDB (embeddings generated automatically).

        Args:
            chunks: List of chunk dicts with 'text', 'id', 'metadata'
            rebuild_bm25: Rebuild BM25 index after adding (can be slow)
        """
        if not chunks:
            return

        logger.info("[ADD] Adding %d chunks to ChromaDB", len(chunks))

        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info("[OK] Added %d chunks (total: %d)", len(chunks), self.collection.count())

        if rebuild_bm25:
            self.rebuild_bm25_index()

    def embed_and_add(
        self,
        documents: list[dict],
        batch_size: Optional[int] = None,
        show_progress: bool = True,
    ) -> int:
        """
        Embed documents and add to ChromaDB.

        Args:
            documents: List of dicts with 'text', 'doc_id', 'metadata'
            batch_size: Override default batch size
            show_progress: Show progress bar

        Returns:
            Number of documents added
        """
        from tqdm import tqdm

        batch_size = batch_size or self.batch_size
        total_added = 0

        iterator = tqdm(
            range(0, len(documents), batch_size),
            desc="Embedding batches",
            unit="batch",
        ) if show_progress else range(0, len(documents), batch_size)

        for batch_start in iterator:
            batch_end = min(batch_start + batch_size, len(documents))
            batch = documents[batch_start:batch_end]

            # Generate embeddings manually
            texts = [d["text"] for d in batch]
            embeddings = self.embedding_fn(texts)

            # Prepare ChromaDB data
            ids = [
                d.get("id") or f"{d['doc_id']}_{batch_start + i:04d}"
                for i, d in enumerate(batch)
            ]
            metadatas = [d.get("metadata", {}) for d in batch]

            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            total_added += len(batch)

        # Rebuild BM25 index
        self.rebuild_bm25_index()

        return total_added

    def search_hybrid(
        self,
        query: str,
        n_results: int = 10,
        alpha: float = 0.7,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Hybrid search: semantic (ChromaDB) + lexical (BM25).

        Args:
            query: Search query
            n_results: Number of results
            alpha: Weight for semantic vs BM25 (1.0=semantic only, 0.0=BM25 only)
            filter_metadata: ChromaDB metadata filter

        Returns:
            List of result dicts with text, score, metadata
        """
        # Get semantic search results from ChromaDB
        semantic_results = self._semantic_search(query, n_results * 2, filter_metadata)

        if not semantic_results:
            return []

        # Get BM25 scores for all retrieved documents
        doc_id_to_result = {r["metadata"].get("doc_id", r["id"]): r for r in semantic_results}

        # Run BM25 search on full corpus
        bm25_results = self.bm25.search(query, top_k=n_results * 2)

        if not bm25_results:
            return semantic_results[:n_results]

        # Score fusion
        max_sem = max(r["score"] for r in semantic_results) if semantic_results else 1.0
        max_bm25 = bm25_results[0][1] if bm25_results else 1.0

        max_sem = max(max_sem, 1e-10)
        max_bm25 = max(max_bm25, 1e-10)

        # Build fused scores
        fused_scores: dict[str, float] = {}

        for r in semantic_results:
            doc_id = r["metadata"].get("doc_id", r["id"])
            norm_sem = r["score"] / max_sem

            # Find BM25 score for this doc
            bm25_score = 0.0
            for bm25_doc_idx, bm25_score_val in bm25_results:
                # Match by approximate position in result list
                if doc_id_to_result:
                    keys = list(doc_id_to_result.keys())
                    try:
                        bm25_idx = int(bm25_doc_idx)
                        if 0 <= bm25_idx < len(keys):
                            bm25_key = keys[bm25_idx]
                            if bm25_key == doc_id:
                                bm25_score = bm25_score_val
                                break
                    except ValueError:
                        pass

            # Normalize BM25 score
            norm_bm25 = bm25_score / max_bm25

            fused_scores[doc_id] = alpha * norm_sem + (1 - alpha) * norm_bm25

        # Sort by fused score
        sorted_results = sorted(
            semantic_results,
            key=lambda r: fused_scores.get(r["metadata"].get("doc_id", r["id"]), 0),
            reverse=True
        )

        # Add search type info to results
        for r in sorted_results[:n_results]:
            doc_id = r["metadata"].get("doc_id", r.get("id", ""))
            r["fused_score"] = fused_scores.get(doc_id, 0)
            r["semantic_score"] = r.get("score", 0)
            r["bm25_score"] = norm_bm25 if doc_id in [k for k in doc_id_to_result] else 0.0

        return sorted_results[:n_results]

    def _semantic_search(
        self,
        query: str,
        n_results: int,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """Run semantic search via ChromaDB."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata,
        )

        search_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                score = 1 - results["distances"][0][i]
                meta = results["metadatas"][0][i] or {}

                # Add superseding warning
                is_superseded = meta.get("is_superseded", False)
                superseded_by = meta.get("superseded_by")

                search_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "score": score,
                    "metadata": meta,
                    "superseded_warning": (
                        f"Dokumen ini sudah dicabut dan digantikan oleh {superseded_by}"
                        if is_superseded and superseded_by else None
                    ),
                })

        return search_results

    def rebuild_bm25_index(self):
        """Rebuild BM25 index from current ChromaDB collection."""
        logger.info("[REBUILD] Rebuilding BM25 index...")
        self.bm25 = self._build_bm25_from_collection()

    def get_stats(self) -> dict:
        """Get embedder statistics."""
        base_stats = {
            "model_name": self.model_name,
            "chromadb_chunks": self.collection.count(),
            "bm25_docs": self.bm25.doc_count,
            "bm25_vocab_size": len(self.bm25.vocab),
        }

        bm25_stats = self.bm25.get_stats()
        return {**base_stats, **bm25_stats}


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Embedder - Embed chunks and manage BM25 index")
    parser.add_argument("--action", choices=["build_bm25", "search", "stats"],
                        default="stats", help="Action to perform")
    parser.add_argument("--query", help="Search query (for search action)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--alpha", type=float, default=0.7,
                        help="Semantic weight (0-1, higher = more semantic)")

    args = parser.parse_args()

    embedder = PipelineEmbedder()

    if args.action == "stats":
        stats = embedder.get_stats()
        print("\n[STAT] Embedder Statistics")
        print("=" * 50)
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.action == "build_bm25":
        embedder.rebuild_bm25_index()
        print("[OK] BM25 index rebuilt")

    elif args.action == "search":
        if not args.query:
            print("[ERR] --query required for search action")
            exit(1)

        results = embedder.search_hybrid(args.query, n_results=args.top_k, alpha=args.alpha)

        print(f"\n[SEARCH] Query: {args.query}")
        print(f"Results: {len(results)}")
        print("=" * 50)
        for i, r in enumerate(results, 1):
            print(f"\n{i}. Score: {r.get('fused_score', r.get('score', 0)):.3f}")
            print(f"   Doc: {r['metadata'].get('doc_id', 'N/A')}")
            print(f"   Text: {r['text'][:150]}...")
            if r.get("superseded_warning"):
                print(f"   ⚠️  {r['superseded_warning']}")