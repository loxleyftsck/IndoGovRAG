"""
Query Understanding Agent
Analyzes user query to extract search parameters: document types,
years, institutions, topics, language, and urgency.
"""

import re
import json
import logging
from typing import Optional

from .base import BaseAgent
from .config import TIMEOUTS, AGENT_PROMPTS

logger = logging.getLogger(__name__)

# ── Rule-based fallback extractor ──────────────────────────────────────────────

_INDONESIAN_URGENT_WORDS = [
    "darurat", "segera", "urgent", "kritis",
]

_ENGLISH_URGENT_WORDS = [
    "urgent", "emergency", "asap", "immediately", "critical",
]

_DOC_TYPE_PATTERNS = {
    "UU": [r"\bUU\s+No\.?\s*\d+/\d+", r"\bUndang[- ]Undang\s+No\.?\s*\d+"],
    "PP": [r"\bPP\s+No\.?\s*\d+/\d+", r"\bPeraturan\s+Pemerintah\s+No\.?\s*\d+"],
    "Perpres": [r"\bPerpres\s+No\.?\s*\d+/\d+", r"\bPeraturan\s+Presiden\s+No\.?\s*\d+"],
    "Permen": [r"\bPermen\s+No\.?\s*\d+/\d+", r"\bPeraturan\s+Menteri\s+No\.?\s*\d+"],
    "Perda": [r"\bPerda\s+(?:kabupaten|kota|provinsi)\s+No\.?\s*\d+", r"\bPeraturan\s+Daerah\s+No\.?\s*\d+"],
    "KEPUTUSAN": [r"\bKeputusan\s+(?:Mentri|Kepala\s+Lembaga)", r"\bKep\s+No\.?\s*\d+"],
    "SE": [r"\bSurat\s+Edaran\s+(?:Mentri|Kepala)", r"\bSE\s+No\.?\s*\d+"],
}

_INSTITUTION_KEYWORDS = [
    "Kementerian Dalam Negeri", "Kemendagri",
    "Kementerian Keuangan", "Kemkeu",
    "Kementerian Hukum dan HAM",
    "Kementerian Agama",
    "Kementerian Pendidikan", "Kemendikbud",
    "Kementerian Kesehatan", "Kemkes",
    "Kementerian Energi dan Sumber Daya Mineral",
    "Kementerian Komunikasi dan Informatika", "Kominfo",
    "BNPB", "BRIN",
    "BPK", "BPKP",
    "MK", "MA", "KY",
    "KPPU", "KPK",
    "DPR", "MPR",
    "BRIN", "BPPT",
    "Lembaga Ilmu Pengetahuan Indonesia",
    "Badan Pusat Statistik", "BPS",
    "Pemda", "Pemkab", "Pemkot", "Gubernur", "Walikota", "Bappeda",
]

_TOPIC_KEYWORDS = [
    "pemilu", "pilkada", "pemilukepala daerah",
    "pajak", "perpajakan", "ppn", "pph", "beacukai",
    "ham", "hak asasi manusia", "perlindungan anak",
    "lingkungan", "AMDAL",
    "hukum", "pidana", "perdata", "agraria", "tanah", "kepemilikan tanah",
    "tenaga kerja", "ketenagakerjaan",
    "kependudukan", "KTP", "KK", "NIK", "adminduk",
    "pendidikan", "sekolah", "negeri",
    "kesehatan", "bpjs", "rumah sakit", "vaksinasi",
    "pertanian", "perternakan", "perikanan", "kelautan",
    "ekonomi", "umkm", "koperasi", "investasi",
    "energi", "minerba", "batu bara", "minyak", "gas", "geotermal",
    "transportasi", "lalu lintas",
]

_YEAR_PATTERN = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")
_YEAR_RANGE_PATTERN = re.compile(r"(19[5-9]\d|20[0-2]\d)\s*[-]\s*(19[5-9]\d|20[0-2]\d)")


def _rule_based_extract(query: str) -> dict:
    """Extract entities using regex/keyword rules when Groq is unavailable."""
    query_lower = query.lower()

    # Language detection
    bahasa = "indonesian"
    if re.search(r"\b(what|who|when|where|why|how)\b", query_lower) and \
       not any(w in query_lower for w in ["apa", "siapa", "kapan", "dimana", "mengapa", "bagaimana"]):
        bahasa = "english"

    # Urgency
    is_urgent = any(w in query_lower for w in _INDONESIAN_URGENT_WORDS) or \
               any(w in query_lower for w in _ENGLISH_URGENT_WORDS)

    # Document types
    jenis_dokumen = None
    for dtype, patterns in _DOC_TYPE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, query, re.IGNORECASE):
                jenis_dokumen = dtype
                break
        if jenis_dokumen:
            break

    # Year range
    tahun_range = None
    range_match = _YEAR_RANGE_PATTERN.search(query)
    if range_match:
        tahun_range = f"{range_match.group(1)}-{range_match.group(2)}"
    else:
        years = _YEAR_PATTERN.findall(query)
        if len(years) >= 2:
            tahun_range = f"{years[0]}-{years[-1]}"
        elif years:
            tahun_range = years[0]

    # Institution
    institusi = None
    for inst in _INSTITUTION_KEYWORDS:
        if inst.lower() in query_lower:
            institusi = inst
            break

    # Topic
    topik = None
    for kw in _TOPIC_KEYWORDS:
        if kw in query_lower:
            topik = kw
            break

    return {
        "jenis_dokumen": jenis_dokumen,
        "tahun_range": tahun_range,
        "institusi": institusi,
        "topik": topik,
        "bahasa": bahasa,
        "is_urgent": is_urgent,
    }


# ── Groq call helper ────────────────────────────────────────────────────────────

def _call_groq(prompt: str, system: str, max_tokens: int = 256, temperature: float = 0.1) -> Optional[str]:
    """Call Groq API with fallback to None on error."""
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
        logger.debug(f"[query_understanding] Groq call failed: {exc}")
        return None


# ── Agent ──────────────────────────────────────────────────────────────────────

class QueryUnderstandingAgent(BaseAgent):
    """Extracts structured search parameters from natural-language queries."""

    name = "query_understanding"
    timeout = TIMEOUTS["query_understanding"]

    async def run(self, context: dict) -> dict:
        query = context.get("query", "").strip()
        if not query:
            context["query_entities"] = {}
            return context

        logger.info(f"[query_understanding] analyzing: {query[:80]}")

        # Attempt Groq-powered extraction
        cfg = AGENT_PROMPTS["query_understanding"]
        prompt = (
            f"Analisis pertanyaan berikut dan ekstrak parameter pencarian (JSON only):\n\n"
            f"Pertanyaan: {query}\n\nJSON:"
        )
        raw = _call_groq(prompt, cfg["system"], cfg["max_tokens"], cfg["temperature"])

        if raw:
            cleaned = re.sub(r"```json\s*", "", raw.strip()).strip()
            cleaned = re.sub(r"```\s*$", "", cleaned).strip()
            try:
                entities = json.loads(cleaned)
                if isinstance(entities, dict):
                    context["query_entities"] = entities
                    logger.info(f"[query_understanding] Groq extracted: {entities}")
                    return context
            except json.JSONDecodeError as exc:
                logger.warning(
                    f"[query_understanding] Groq returned invalid JSON: {exc}; "
                    "falling back to rules"
                )

        # Rule-based fallback
        entities = _rule_based_extract(query)
        context["query_entities"] = entities
        logger.info(f"[query_understanding] rule-based: {entities}")
        return context