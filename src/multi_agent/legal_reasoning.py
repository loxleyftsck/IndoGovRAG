"""
Legal Reasoning Agent
Analyzes retrieved chunks for conflicts, superseded laws, revisions, and groupings.
Calls Groq API for structured legal analysis; falls back to keyword-based heuristics.
"""

import re
import json
import logging
from typing import Optional

from .base import BaseAgent
from .config import TIMEOUTS, AGENT_PROMPTS

logger = logging.getLogger(__name__)

# Keywords that indicate a law has been superseded, revised, or repealed
_SUPERSEDED_PATTERNS = [
    (re.compile(r"\b(ditetapkan|disahkan)\s+(?:sebagai)?\s*(?:UU|Peraturan)\s+No", re.IGNORECASE), "perubahan_baru"),
    (re.compile(r"\b(UU|Peraturan)\s+(?:yang\s+)?(?:telah\s+)?diubah\s+(?:oleh)\s+(\w+\s+\d+/\d+)", re.IGNORECASE), "diubah"),
    (re.compile(r"\b(UU|Peraturan)\s+(?:yang\s+)?(?:telah\s+)?dicabut\s+(?:oleh)\s+(\w+\s+\d+/\d+)", re.IGNORECASE), "dicabut"),
    (re.compile(r"\b(UU|Peraturan)\s+(\d+/\d+)\s+(?:secara\s+)?(?:telah\s+)?dicabut", re.IGNORECASE), "dicabut"),
    (re.compile(r"\bperubahan\s+(?:terhadap|atas)\s+(\w+\s+\d+/\d+)", re.IGNORECASE), "diubah"),
    (re.compile(r"\brevisi\s+(?:terhadap|atas)\s+(\w+\s+\d+/\d+)", re.IGNORECASE), "diubah"),
    (re.compile(r"\bammandemen\b", re.IGNORECASE), "diubah"),
    (re.compile(r"\bperubahan\s+kedua\b", re.IGNORECASE), "perubahan_kedua"),
    (re.compile(r"\bperubahan\s+ketiga\b", re.IGNORECASE), "perubahan_ketiga"),
    (re.compile(r"\bperubahan\s+keempat\b", re.IGNORECASE), "perubahan_keempat"),
    (re.compile(r"\bperubahan\s+kelima\b", re.IGNORECASE), "perubahan_kelima"),
]

_CONFLICT_PATTERNS = [
    (re.compile(r"\b(bertentangan|konflik|melisih)", re.IGNORECASE), "konflik"),
    (re.compile(r"\btidak\s+(?:sejalan|d engan)\s+(?:peraturan|hukum)", re.IGNORECASE), "konflik"),
    (re.compile(r"\bdiatur\s+(?:secara\s+)?berbeda", re.IGNORECASE), "perbedaan_pengaturan"),
]


def _extract_doc_refs(text: str) -> list:
    """Extract document references from chunk text."""
    refs = []
    patterns = [
        r"(?:UU|Peraturan\s+Pemerintah|Perpres|Permen|Perda|Keputusan|Surat\s+Edaran)\s+No\.?\s*(\d+/\d+)",
        r"(?:UU|Peraturan)\s+No\.?\s*(\d+)\s+(?:Tahun\s+)?(?:Tahun\s+)?(\d{4})",
        r"(?:Undang[- ]Undang)\s+(?:Nomor\s+)?(\d+)\s+(?:Tahun\s+)?(?:Tahun\s+)?(\d{4})",
    ]
    for pat in patterns:
        for match in pat.finditer(text):
            ref = " ".join(g for g in match.groups() if g)
            if ref:
                refs.append(ref.strip())
    return list(dict.fromkeys(refs))  # deduplicate


def _rule_based_analyze(chunks: list) -> dict:
    """Keyword/regex-based legal analysis when Groq is unavailable."""
    if not chunks:
        return {"analisis": [], "group_by_law": {}, "confidence": 0.3}

    analisis = []
    group_by_law = {}
    warnings = []

    for chunk in chunks:
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})
        doc_id = metadata.get("doc_id", metadata.get("source", "unknown"))

        entry = {
            "doc_id": doc_id,
            "dokumen": metadata.get("title", doc_id),
            "status_geothermal": "normatif",
            "perubahan": None,
            "konflik": None,
            "alasan": None,
        }

        # Check superseded patterns
        for pat, label in _SUPERSEDED_PATTERNS:
            if pat.search(text):
                entry["perubahan"] = f"Terdeteksi indikasi: {label}"
                warnings.append(f"Dokumen {doc_id} mungkin telah mengalami {label}")
                break

        # Check conflict patterns
        for pat, label in _CONFLICT_PATTERNS:
            if pat.search(text):
                entry["konflik"] = f"Terdeteksi: {label}"
                warnings.append(f"Dokumen {doc_id} mungkin berkonflik dengan peraturan lain")
                break

        # Group by law
        refs = _extract_doc_refs(text)
        for ref in refs:
            if ref not in group_by_law:
                group_by_law[ref] = []
            group_by_law[ref].append(f"chunk:{metadata.get('chunk_id', '?')}")

        analisis.append(entry)

    # Confidence based on how many chunks have indicators
    confidence = min(0.3 + (len(warnings) * 0.1), 0.8) if warnings else 0.5

    return {
        "analisis": analisis,
        "group_by_law": group_by_law,
        "warnings": warnings,
        "confidence": round(confidence, 2),
    }


def _call_groq(prompt: str, system: str, max_tokens: int = 768, temperature: float = 0.1) -> Optional[str]:
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
        logger.debug(f"[legal_reasoning] Groq call failed: {exc}")
        return None


# ── Agent ──────────────────────────────────────────────────────────────────────

class LegalReasoningAgent(BaseAgent):
    """
    Analyzes retrieved chunks for legal relationships:
    superseded, revised, conflicting laws. Groups by document.
    """

    name = "legal_reasoning"
    timeout = TIMEOUTS["legal_reasoning"]

    async def run(self, context: dict) -> dict:
        chunks = context.get("chunks", [])

        if not chunks:
            logger.warning("[legal_reasoning] No chunks to analyze")
            context["legal_analysis"] = {"analisis": [], "group_by_law": {}, "confidence": 0.0}
            return context

        logger.info(f"[legal_reasoning] analyzing {len(chunks)} chunks")

        # Build context text for Groq
        context_texts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            doc_id = meta.get("doc_id", meta.get("source", f"chunk-{i}"))
            context_texts.append(
                f"[{i}] Dokumen: {doc_id}\n"
                f"Tahun: {meta.get('year', '?')}\n"
                f"Jenis: {meta.get('doc_type', '?')}\n"
                f"Konten:\n{chunk.get('text', '')[:600]}"
            )

        combined = "\n\n".join(context_texts)

        # Attempt Groq analysis
        cfg = AGENT_PROMPTS["legal_reasoning"]
        prompt = (
            f"Analisis {len(chunks)} potongan dokumen hukum berikut:\n\n"
            f"{combined}\n\n"
            "Kembalikan JSON valid tanpa markdown fences."
        )

        raw = _call_groq(prompt, cfg["system"], cfg["max_tokens"], cfg["temperature"])

        if raw:
            cleaned = re.sub(r"```json\s*", "", raw.strip()).strip()
            cleaned = re.sub(r"```\s*$", "", cleaned).strip()
            try:
                analysis = json.loads(cleaned)
                context["legal_analysis"] = analysis
                logger.info(f"[legal_reasoning] Groq analysis done, confidence={analysis.get('confidence', '?')}")
                return context
            except json.JSONDecodeError as exc:
                logger.warning(f"[legal_reasoning] Groq returned invalid JSON: {exc}; falling back to rules")

        # Rule-based fallback
        analysis = _rule_based_analyze(chunks)
        context["legal_analysis"] = analysis
        logger.info(f"[legal_reasoning] rule-based confidence={analysis['confidence']}")
        return context