"""
Legal Q&A System for IndoGovRAG

Conversational legal Q&A built on top of the existing RAG pipeline.
Delivers natural-language answers with proper citations and confidence scores.

Example usage:
    >>> from src.legal.legal_qa import LegalQA
    >>> qa = LegalQA()
    >>> result = qa.ask("Apa perbedaan PT dan CV?")
    >>> print(result.answer)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from src.rag.pipeline import RAGPipeline
from src.legal.citation_formatter import (
    CitationSource,
    format_citation,
    format_sources,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response dataclass
# ---------------------------------------------------------------------------

@dataclass
class LegalQAResult:
    """
    Structured response from LegalQA.ask().

    Attributes:
        question      : Original user question.
        answer         : Generated answer text.
        confidence     : Overall confidence score (0–1).
        sources        : List of source dicts from retrieval.
        retrieved_chunks : Raw chunks used for generation.
        response_time_ms : Time taken to generate (milliseconds).
        model_used     : LLM model that generated the answer.
        from_cache     : Whether the result came from the query cache.
    """
    question: str
    answer: str
    confidence: float
    sources: list[dict]
    retrieved_chunks: list[dict]
    response_time_ms: float
    model_used: str = ""
    from_cache: bool = False

    def formatted_sources(self, fmt: str = "plain", include_confidence: bool = True) -> str:
        """
        Return a formatted multi-line string of sources.

        Args:
            fmt                : "plain", "markdown", or "apa".
            include_confidence : Show confidence scores.

        Returns:
            Formatted source block.
        """
        return format_sources(
            self.sources,
            fmt=fmt,
            include_confidence=include_confidence,
        )

    def citation_list(self) -> list[CitationSource]:
        """
        Convert sources to CitationSource objects.
        """
        results = []
        for src in self.sources:
            num = src.get("doc_id", "?")
            # Try to extract number from doc_id like "UU-13-2008"
            if "-" in num:
                parts = num.split("-")
                if len(parts) >= 2:
                    num = parts[1]
            results.append(
                CitationSource(
                    doc_type=src.get("doc_type", "UU"),
                    number=num,
                    year=src.get("year", ""),
                    title="",
                    confidence=src.get("score", 0.0),
                    doc_id=src.get("doc_id", ""),
                )
            )
        return results

    def __str__(self) -> str:
        conf_bar = "".join(
            "=" if i < int(self.confidence * 10) else "-"
            for i in range(10)
        )
        cache_tag = " [CACHED]" if self.from_cache else ""
        lines = [
            f"Q: {self.question}",
            f"A: {self.answer}",
            f"Confidence: [{conf_bar}] {self.confidence:.0%}{cache_tag}",
            "",
            "Sources:",
            self.formatted_sources(fmt="plain", include_confidence=True),
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class LegalQA:
    """
    Conversational legal Q&A for Indonesian government documents.

    Wraps the existing RAGPipeline and adds:
    - Structured LegalQAResult responses
    - Confidence scoring
    - Formatted citation output
    - Query caching (inherited from RAGPipeline)

    Example:
        >>> qa = LegalQA()
        >>> result = qa.ask("Berapa lama proses pailit?")
        >>> print(result.answer)
        >>> print(result.formatted_sources("markdown"))
    """

    def __init__(
        self,
        pipeline: Optional[RAGPipeline] = None,
        top_k: int = 5,
        min_confidence: float = 0.3,
    ):
        """
        Initialize LegalQA.

        Args:
            pipeline        : Existing RAGPipeline instance. Created automatically
                             if None (reads API keys from environment).
            top_k           : Number of chunks to retrieve per query.
            min_confidence  : Minimum confidence threshold below which
                             a low-confidence warning is added to the answer.
        """
        self.top_k = top_k
        self.min_confidence = min_confidence

        if pipeline is not None:
            self.pipeline = pipeline
        else:
            logger.info("[LegalQA] No pipeline provided — creating default RAGPipeline")
            self.pipeline = RAGPipeline(top_k=top_k)

        logger.info("[LegalQA] Legal Q&A system initialised")
        logger.info(f"   Top-K: {top_k}")
        logger.info(f"   Min confidence: {min_confidence}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(
        self,
        question: str,
        filter_metadata: Optional[dict] = None,
        include_sources: bool = True,
    ) -> LegalQAResult:
        """
        Ask a legal question and receive a structured answer with citations.

        Args:
            question         : Natural-language legal question in Indonesian.
            filter_metadata  : Optional metadata filter for retrieval.
            include_sources  : Include source citations in response.

        Returns:
            LegalQAResult with answer, sources, confidence, and timing.

        Example:
            >>> result = qa.ask("Persyaratan pengesahan PT")
            >>> print(result.answer)
            >>> print(result.formatted_sources("markdown"))
        """
        t0 = time.time()

        logger.info(f"[LegalQA] Q: {question}")

        # Delegate to underlying RAG pipeline
        raw = self.pipeline.query(
            question=question,
            filter_metadata=filter_metadata,
            include_sources=include_sources,
            use_cache=True,
        )

        elapsed_ms = (time.time() - t0) * 1000

        # Derive overall confidence from retrieved chunk scores
        scores = [c["score"] for c in raw.get("retrieved_chunks", [])]
        confidence = sum(scores) / len(scores) if scores else 0.0

        # Low-confidence augmentation
        answer = raw.get("answer", "")
        if confidence < self.min_confidence:
            answer = (
                "[PERHATIAN: Informasi dengan tingkat keyakinan rendah. "
                "Silakan verifikasi dengan sumber resmi]\n\n"
                + answer
            )
            logger.warning(
                f"[LegalQA] Low confidence ({confidence:.2f}) for: {question[:60]}"
            )

        return LegalQAResult(
            question=question,
            answer=answer,
            confidence=confidence,
            sources=raw.get("sources", []),
            retrieved_chunks=raw.get("retrieved_chunks", []),
            response_time_ms=elapsed_ms,
            model_used=raw.get("model_used", ""),
            from_cache=raw.get("from_cache", False),
        )

    def ask_batch(
        self,
        questions: list[str],
        filter_metadata: Optional[dict] = None,
    ) -> list[LegalQAResult]:
        """
        Answer multiple questions in sequence.

        Args:
            questions       : List of questions.
            filter_metadata  : Shared metadata filter.

        Returns:
            List of LegalQAResult, one per question.
        """
        return [self.ask(q, filter_metadata=filter_metadata) for q in questions]

    def get_stats(self) -> dict:
        """Return pipeline statistics."""
        return self.pipeline.get_stats()


# ---------------------------------------------------------------------------
# Convenience functions (functional API)
# ---------------------------------------------------------------------------

def ask_legal(question: str, **kwargs) -> LegalQAResult:
    """
    One-shot legal Q&A.

    Creates a LegalQA instance internally and returns the result.
    Suitable for simple scripts and API routes.

    Example:
        >>> result = ask_legal("Apa itu NIB?")
        >>> print(result.answer)
    """
    qa = LegalQA(**kwargs)
    return qa.ask(question)


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    print("=" * 70)
    print("Legal Q&A System — Self-Test")
    print("=" * 70)

    # Check if vector store has data
    try:
        from src.retrieval.vector_search import VectorStore
        store = VectorStore()
        has_data = store.collection.count() > 0
    except Exception as e:
        logger.warning(f"Could not connect to vector store: {e}")
        has_data = False

    if not has_data:
        print(
            "[WARN] Vector store is empty. "
            "Run the ingestion pipeline first to add documents."
        )
        print("Demonstrating LegalQAResult formatting with mock data instead.\n")

        # Show formatting with mock data so the module is still testable
        mock_result = LegalQAResult(
            question="Berapa lama proses pembuatan NIB?",
            answer=(
                "Proses pembuatan NIB melalui sistem OSS (Online Single Submission) "
                "adalah 1x24 jam setelah dokumen lengkap disubmit."
            ),
            confidence=0.92,
            sources=[
                {
                    "doc_id": "Permenkumham-5-2019",
                    "doc_type": "Permen",
                    "year": "2019",
                    "score": 0.92,
                },
                {
                    "doc_id": "PP-24-2018",
                    "doc_type": "PP",
                    "year": "2018",
                    "score": 0.88,
                },
            ],
            retrieved_chunks=[],
            response_time_ms=312.5,
            model_used="groq",
            from_cache=False,
        )

        print(mock_result)
        print("\n--- Markdown format ---")
        print(mock_result.formatted_sources("markdown"))
        print("\n--- APA format ---")
        print(mock_result.formatted_sources("apa"))

        print("\n--- CitationSource list ---")
        for cs in mock_result.citation_list():
            print(f"  {format_citation(cs, fmt='plain')}")

        print("\n--- Demo questions (would run against pipeline) ---")
        demo_questions = [
            "Apa perbedaan PT dan CV?",
            "Berapa lama proses pailit?",
            "Persyaratan pengesahan PT",
        ]
        for q in demo_questions:
            print(f"  Q: {q}")

    else:
        print("[OK] Vector store connected. Running live demo.\n")
        qa = LegalQA(top_k=3)

        demo_questions = [
            "Apa perbedaan PT dan CV?",
            "Berapa lama proses pailit?",
            "Persyaratan pengesahan PT",
        ]

        for question in demo_questions:
            result = qa.ask(question)
            print(result)
            print("-" * 70)

        stats = qa.get_stats()
        print(f"\n[STATS] {stats}")
