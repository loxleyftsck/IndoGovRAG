"""
Response Synthesis Agent
Generates the final Indonesian-language answer with citations,
warnings, and confidence assessment.
"""

import re
import json
import logging
from typing import Optional

from .base import BaseAgent
from .config import TIMEOUTS, AGENT_PROMPTS

logger = logging.getLogger(__name__)


def _format_sources(chunks: list) -> list:
    """Format source list from chunks for citation."""
    seen = set()
    sources = []

    for chunk in chunks:
        meta = chunk.get("metadata", {})
        doc_id = meta.get("doc_id", meta.get("source", "Unknown"))
        if doc_id in seen:
            continue
        seen.add(doc_id)

        doc_type = meta.get("doc_type", "")
        year = meta.get("year", "")

        if doc_type and year:
            label = f"{doc_id} ({doc_type}, {year})"
        elif doc_type:
            label = f"{doc_id} ({doc_type})"
        else:
            label = doc_id

        sources.append(label)

    return sources


def _extract_confidence_from_answer(answer: str, chunks: list) -> float:
    """Estimate confidence from answer quality signals and chunk scores."""
    score = 0.6  # baseline

    # Penalize hedged answers
    hedge_count = len(re.findall(
        r"\b(tidak\s+tersedia|tidak\s+ditemukan|maaf|tidak\s+yakin|mungkin|belum\s+jelas)",
        answer.lower()
    ))
    score -= hedge_count * 0.05

    # Reward citations
    citation_count = len(re.findall(r"\b(UU|Perpres|PP|Permen|Perda)\s+No\.?\s*\d+/\d+", answer))
    score += min(citation_count * 0.05, 0.15)

    # Penalize empty or very short answers
    if len(answer.strip()) < 50:
        score -= 0.15

    # Factor in retrieval scores
    chunk_scores = [c.get("score", 0.0) for c in chunks]
    if chunk_scores:
        avg_chunk_score = sum(chunk_scores) / len(chunk_scores)
        score = (score * 0.4) + (avg_chunk_score * 0.6)

    return max(0.0, min(1.0, round(score, 3)))


def _call_groq(prompt: str, system: str, max_tokens: int = 1024, temperature: float = 0.2) -> Optional[str]:
    """Call Groq API, returning None on failure."""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None

        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.debug(f"[response_synthesis] Groq call failed: {exc}")
        return None


# ── Agent ──────────────────────────────────────────────────────────────────────

class ResponseSynthesisAgent(BaseAgent):
    """
    Generates the final answer in Indonesian with structured citations,
    legal warnings, and confidence scoring.
    """

    name = "response_synthesis"
    timeout = TIMEOUTS["response_synthesis"]

    async def run(self, context: dict) -> dict:
        query = context.get("query", "")
        chunks = context.get("chunks", [])
        legal_analysis = context.get("legal_analysis", {})
        query_entities = context.get("query_entities", {})

        if not query:
            context["final_answer"] = "Pertanyaan tidak valid."
            context["confidence"] = 0.0
            return context

        logger.info(f"[response_synthesis] generating answer for: {query[:80]}")

        # No chunks — give a graceful no-result response
        if not chunks:
            logger.warning("[response_synthesis] No chunks retrieved")
            context["final_answer"] = (
                "Maaf, saya tidak menemukan informasi yang relevan dalam dokumen "
                "untuk pertanyaan Anda. Silakan coba rumusan pertanyaan yang berbeda."
            )
            context["confidence"] = 0.0
            context["sources"] = []
            context["warnings"] = ["Tidak ada dokumen yang ditemukan."]
            return context

        # Build context text for generation
        context_blocks = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            doc_id = meta.get("doc_id", meta.get("source", f"dokumen-{i}"))
            doc_type = meta.get("doc_type", "")
            year = meta.get("year", "")
            score = chunk.get("score", 0.0)
            context_blocks.append(
                f"[SUMBER {i}] {doc_id}"
                + (f" ({doc_type}, {year})" if (doc_type or year) else "")
                + f" | Relevance: {score:.2f}\n"
                + chunk.get("text", "")[:800]
            )

        combined_chunks = "\n\n".join(context_blocks)

        # Include legal analysis if available
        analysis_note = ""
        if legal_analysis and legal_analysis.get("analisis"):
            analysis_note = (
                "\n\n[ANALISIS HUKUM]\n"
                + json.dumps(legal_analysis, ensure_ascii=False, indent=2)
            )

        # Build prompt
        cfg = AGENT_PROMPTS["response_synthesis"]
        prompt = (
            f"[CONTEXT]\n{combined_chunks}{analysis_note}\n[END CONTEXT]\n\n"
            f"[PERTANYAAN]\n{query}\n[END PERTANYAAN]\n\n"
            f"Bahas dalam Bahasa Indonesia Baku. "
            f"Jawab berdasarkan [CONTEXT] saja. Jangan tambahkan informasi di luar konteks."
        )

        # Attempt Groq generation
        answer = _call_groq(prompt, cfg["system"], cfg["max_tokens"], cfg["temperature"])

        if not answer:
            # Fallback: raw concatenated chunks (no LLM)
            answer = self._build_fallback_answer(query, chunks, legal_analysis)
            logger.info("[response_synthesis] Using fallback answer (Groq unavailable)")

        # Confidence estimation
        confidence = _extract_confidence_from_answer(answer, chunks)

        # Build warnings from legal analysis
        warnings = []
        if legal_analysis:
            for entry in legal_analysis.get("analisis", []):
                if entry.get("perubahan"):
                    warnings.append(f"Perhatikan: {entry['doc_id']} {entry['perubahan']}")
                if entry.get("konflik"):
                    warnings.append(f"Peringatan: Konflik terdeteksi pada {entry['doc_id']}")

        # Sources
        sources = _format_sources(chunks)

        # Assemble final result
        context["final_answer"] = answer
        context["confidence"] = confidence
        context["sources"] = sources
        context["warnings"] = warnings[:5]  # cap at 5 warnings
        context["response_generation_method"] = "groq" if answer and len(answer) > 200 else "fallback"

        logger.info(
            f"[response_synthesis] done | confidence={confidence:.2f} | "
            f"sources={len(sources)} | warnings={len(warnings)}"
        )
        return context

    def _build_fallback_answer(self, query: str, chunks: list, legal_analysis: dict) -> str:
        """Build a structured fallback answer without LLM."""
        lines = [f"## Jawaban: {query}\n"]

        lines.append("Berdasarkan dokumen yang ditemukan:\n")

        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            doc_id = meta.get("doc_id", meta.get("source", f"Sumber {i}"))
            lines.append(f"\n### Sumber {i}: {doc_id}")
            text = chunk.get("text", "")
            lines.append(text[:600] + ("..." if len(text) > 600 else ""))

        if legal_analysis and legal_analysis.get("warnings"):
            lines.append("\n## Peringatan")
            for w in legal_analysis["warnings"][:3]:
                lines.append(f"- {w}")

        lines.append(
            "\n---\n*Jawaban ini disusun secara otomatis dari dokumen tanpa pemrosesan LLM lanjutan. "
            "Untuk hasil terbaik, pastikan Groq API key dikonfigurasi.*"
        )
        return "\n".join(lines)