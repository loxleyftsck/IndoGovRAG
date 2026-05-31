"""
Retrieval Agent
Queries ChromaDB using the existing RAG pipeline (hybrid search: vector + BM25).
Returns top-K chunks with similarity scores and source metadata.
"""

import logging
from typing import Optional

from .base import BaseAgent
from .config import TIMEOUTS

logger = logging.getLogger(__name__)


def _build_filter_metadata(query_entities: dict) -> Optional[dict]:
    """Build a ChromaDB where clause from extracted query entities."""
    conditions = []

    if query_entities.get("jenis_dokumen"):
        conditions.append({"doc_type": {"$eq": query_entities["jenis_dokumen"]}})

    if query_entities.get("institusi"):
        inst = query_entities["institusi"]
        conditions.append({
            "$or": [
                {"institusi": {"$eq": inst}},
                {"source": {"$contains": inst}},
            ]
        })

    if query_entities.get("tahun_range"):
        years = query_entities["tahun_range"]
        if isinstance(years, str) and "-" in years:
            parts = years.split("-")
            if len(parts) == 2:
                try:
                    conditions.append({
                        "year": {
                            "$gte": int(parts[0]),
                            "$lte": int(parts[1]),
                        }
                    })
                except ValueError:
                    pass

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions} if conditions else None


# ── Agent ──────────────────────────────────────────────────────────────────────

class RetrievalAgent(BaseAgent):
    """
    Retrieves relevant document chunks from ChromaDB.

    Uses the existing RAG pipeline (VectorStore with hybrid search) when available,
    or falls back to a lightweight direct ChromaDB query.
    """

    name = "retrieval"
    timeout = TIMEOUTS["retrieval"]

    async def run(self, context: dict) -> dict:
        query = context.get("query", "")
        entities = context.get("query_entities", {})
        top_k = context.get("options", {}).get("top_k", 5)

        if not query:
            context["retrieval_error"] = "No query provided"
            return context

        logger.info(f"[retrieval] searching top_k={top_k} for: {query[:80]}")

        try:
            # Try to use the existing RAG pipeline
            try:
                from src.rag.pipeline import RAGPipeline
                pipeline = RAGPipeline()
                logger.info("[retrieval] using RAGPipeline (hybrid search)")

                # Build filter from entities
                filter_meta = _build_filter_metadata(entities)

                # Use pipeline's vector_store directly (avoids LLM call)
                if hasattr(pipeline, "vector_store") and pipeline.vector_store:
                    vs = pipeline.vector_store

                    if hasattr(vs, "hybrid_search"):
                        results = vs.hybrid_search(
                            query=query,
                            n_results=top_k,
                            alpha=0.7,
                            filter_metadata=filter_meta,
                        )
                    else:
                        results = vs.search(
                            query=query,
                            n_results=top_k,
                            filter_metadata=filter_meta,
                        )

                    chunks = _normalize_results(results)
                    context["chunks"] = chunks
                    context["retrieval_method"] = "hybrid"

                    logger.info(f"[retrieval] found {len(chunks)} chunks via RAGPipeline")
                    return context

            except Exception as pipeline_error:
                logger.warning(f"[retrieval] RAGPipeline unavailable ({pipeline_error}), "
                                "using direct ChromaDB")

            # Direct ChromaDB fallback
            from src.retrieval.vector_search import VectorStore

            vs = VectorStore()
            if hasattr(vs, "hybrid_search"):
                results = vs.hybrid_search(
                    query=query,
                    n_results=top_k,
                    alpha=0.7,
                    filter_metadata=None,
                )
            else:
                results = vs.search(query=query, n_results=top_k)

            chunks = _normalize_results(results)
            context["chunks"] = chunks
            context["retrieval_method"] = "direct_chromadb"

            logger.info(f"[retrieval] direct ChromaDB returned {len(chunks)} chunks")
            return context

        except Exception as exc:
            logger.error(f"[retrieval] failed: {exc}")
            context["retrieval_error"] = str(exc)
            context["chunks"] = []
            return context


def _normalize_results(results) -> list:
    """Normalize vector store results into a uniform list of chunk dicts."""
    if not results:
        return []

    chunks = []
    for item in results:
        if hasattr(item, "text"):
            chunks.append({
                "text": item.text,
                "metadata": getattr(item, "metadata", {}),
                "score": getattr(item, "score", 0.0),
            })
        elif isinstance(item, dict):
            chunks.append({
                "text": item.get("text", item.get("content", "")),
                "metadata": item.get("metadata", {}),
                "score": item.get("score", item.get("distance", 0.0)),
            })
        else:
            logger.warning(f"[retrieval] unknown result type: {type(item)}")

    return chunks