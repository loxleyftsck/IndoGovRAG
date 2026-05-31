"""
Indonesian Legal Citation Formatter

Formats citations according to Indonesian legal citation standards
(adapted from Bluebook for Indonesian context).

Supported document types:
- UU : Undang-Undang
- PP      : Peraturan Pemerintah
- Perpres : Peraturan Presiden
- Permen  : Peraturan Menteri
- Perda : Peraturan Daerah
- Kepmen  : Keputusan Menteri
- SK : Surat Keputusan
- MOU : Memorandum of Understanding
- Nota   : Nota Kesepahaman
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Document type registry
# ---------------------------------------------------------------------------

class DocType(Enum):
    """Indonesian legal document types."""
    UU      = "Undang-Undang"
    PP = "Peraturan Pemerintah"
    PERPRES = "Peraturan Presiden"
    PERMEN  = "Peraturan Menteri"
    PERDA   = "Peraturan Daerah"
    PERDA_PROV = "Peraturan Daerah Provinsi"
    PERDA_KOT = "Peraturan Daerah Kota/Kabupaten"
    KEPMEN  = "Keputusan Menteri"
    SK = "Surat Keputusan"
    MOU = "Memorandum of Understanding"
    NOTA    = "Nota Kesepahaman"
    PM      = "Peraturan Bersama"
    IN = "Instruksi Presiden"
    PPNS = "Peraturan Pengganti Undang-Undang"
    UUD     = "Undang-Undang Dasar"
    KMA = "Keputusan Menteri Agama"
    SE      = "Surat Edaran"


# ---------------------------------------------------------------------------
# Citation component dataclass
# ---------------------------------------------------------------------------

@dataclass
class CitationSource:
    """
    Structured citation data extracted from metadata or raw string.

    Attributes:
        doc_type    : Document type (e.g. "UU", "PP")
        number      : Regulation number (e.g. "13", "5")
        year        : Year of enactment (e.g. "2008", "2021")
        title       : Full title of the regulation
        articles    : List of article references (e.g. ["Pasal 11", "Pasal 27 ayat (1)"])
        section     : Optional section/chapter reference
        institution : Issuing institution (e.g. "Kementerian Hukum dan HAM")
        url : Optional official URL
        confidence : Confidence score 0-1 from retrieval
        doc_id      : Internal document ID in vector store
    """
    doc_type: str
    number: str
    year: str
    title: str = ""
    articles: list[str] = field(default_factory=list)
    section: str = ""
    institution: str = ""
    url: str = ""
    confidence: float = 0.0
    doc_id: str = ""

    @property
    def short_label(self) -> str:
        """Short citation label, e.g. 'UU 13/2008'."""
        return f"{self.doc_type} {self.number}/{self.year}"

    @property
    def doc_type_full(self) -> str:
        """Full document type name."""
        try:
            return DocType[self.doc_type.upper().replace("-", "_")].value
        except KeyError:
            return self.doc_type


# ---------------------------------------------------------------------------
# Internal parsing helpers
# ---------------------------------------------------------------------------

# Regex patterns for extracting citation components
_PATTERNS = {
    "uu": re.compile(
        r"(?:Undang[-\s]?Undang|UU|U[-\s]?U)\s*(?:No\.?\s*)?(\d+)\s*/\s*(\d{4})",
        re.IGNORECASE
    ),
    "pp": re.compile(
        r"(?:Peraturan\s*Pemerintah|PP)\s*(?:No\.?\s*)?(\d+)\s*/\s*(\d{4})",
        re.IGNORECASE
    ),
    "perpres": re.compile(
        r"(?:Peraturan\s*Presiden|Perpres)\s*(?:No\.?\s*)?(\d+)\s*/\s*(\d{4})",
        re.IGNORECASE
    ),
    "permen": re.compile(
        r"(?:Peraturan\s*Menteri|Permen)(?:\s+[A-Z]+)?\s*(?:No\.?\s*)?(\d+)\s*/\s*(\d{4})",
        re.IGNORECASE
    ),
    "perda": re.compile(
        r"(?:Peraturan\s*Daerah|Perda)\s*(?:No\.?\s*)?(\d+)\s*/\s*(\d{4})",
        re.IGNORECASE
    ),
    "kepmen": re.compile(
        r"(?:Keputusan\s*Menteri|Kepmen)\s*(?:No\.?\s*)?(\d+)\s*/\s*(\d{4})",
        re.IGNORECASE
    ),
    "pasal": re.compile(
        r"(?:Pasal|Pasal\s+Nr\.?)\s*(\d+)\s*(?:ayat\s*\(?\s*(\d+)\s*\)?)?",
        re.IGNORECASE
    ),
    "year": re.compile(r"\b(20\d{2}|19\d{2})\b"),
    "nomor": re.compile(r"(?:No\.?\s*|#)\s*(\d+)", re.IGNORECASE),
}


def _parse_raw(raw: str) -> Optional[CitationSource]:
    """
    Attempt to extract structured data from a raw citation string.

    Returns None if the string cannot be parsed.
    """
    raw = raw.strip()
    if not raw:
        return None

    # Try each doc-type pattern in priority order
    for dtype, pattern in [
        ("UU",      _PATTERNS["uu"]),
        ("PP",      _PATTERNS["pp"]),
        ("Perpres", _PATTERNS["perpres"]),
        ("Permen",  _PATTERNS["permen"]),
        ("Perda",   _PATTERNS["perda"]),
        ("Kepmen",  _PATTERNS["kepmen"]),
    ]:
        m = pattern.search(raw)
        if m:
            title = raw
            # Try to strip the matched portion from the title
            title = pattern.sub("", title).strip(" ,;:-").strip()
            if title.lower().startswith(("tentang", "of", "of the")):
                title = title[7:].strip()
            return CitationSource(
                doc_type=dtype,
                number=m.group(1),
                year=m.group(2),
                title=title,
            )

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_citation(
    raw: str | CitationSource,
    fmt: str = "plain",
    include_confidence: bool = False,
) -> str:
    """
    Format a legal citation string into a human-readable form.

    Args:
        raw : Raw citation string (e.g. "UU13/2008 tentang...")
 or a CitationSource object.
        fmt             : Output format — one of "plain", "markdown", "apa".
        include_confidence : Append confidence score if True.

    Returns:
        Formatted citation string.

    Examples:
        >>> format_citation("UU 13/2008 tentang Rencana Induk Nasional")
        'UU No. 13 Tahun 2008 tentang Rencana Induk Nasional'

        >>> format_citation("UU 13/2008", fmt="markdown")
        '*UU No. 13 Tahun 2008*'

        >>> format_citation("PP 5/2021", fmt="apa")
        'Peraturan Pemerintah No. 5 Tahun 2021.'
    """
    # Normalise to CitationSource
    if isinstance(raw, str):
        src = _parse_raw(raw)
        if src is None:
            return raw  # Return as-is if unparseable
    else:
        src = raw

    dt_label = src.doc_type.upper()
    dt_full  = src.doc_type_full

    # ---- Plain text --------------------------------------------------------
    if fmt == "plain":
        parts = []
        if dt_label in ("UU", "PP", "PERPRES", "PERMEN", "PERDA", "KEPMEN"):
            parts.append(f"{dt_full} No. {src.number} Tahun {src.year}")
        else:
            parts.append(f"{dt_full} No. {src.number} Tahun {src.year}")

        if src.title:
            parts.append(f"tentang {src.title}")

        base = " ".join(parts)

        citation_text = base
        if src.articles:
            article_str = " ".join(src.articles)
            citation_text = f"{base}, {article_str}"

        if include_confidence and src.confidence > 0:
            citation_text += f" (Confidence: {src.confidence:.2f})"

        return citation_text

    # ---- Markdown ---------------------------------------------------------
    if fmt == "markdown":
        if dt_label in ("UU", "PP", "PERPRES", "PERMEN", "PERDA", "KEPMEN"):
            label = f"*{dt_full} No. {src.number} Tahun {src.year}*"
        else:
            label = f"*{dt_full} No. {src.number} Tahun {src.year}*"

        if src.title:
            label += f" tentang {src.title}"

        if src.articles:
            label += f" \n> {' '.join(src.articles)}"

        if include_confidence and src.confidence > 0:
            label += f"  \n> Confidence: `{src.confidence:.2f}`"

        return label

    # ---- APA (Indonesian adapted) ----------------------------------------
    if fmt == "apa":
        parts = []
        if dt_label in ("UU", "PP", "PERPRES", "PERMEN", "PERDA", "KEPMEN"):
            parts.append(f"{dt_full} No. {src.number} Tahun {src.year}.")
        else:
            parts.append(f"{dt_full} No. {src.number} Tahun {src.year}.")

        if src.title:
            parts.append(src.title + ".")

        if src.articles:
            parts.append(" ".join(src.articles) + ".")

        result = " ".join(parts)
        if include_confidence and src.confidence > 0:
            result += f" (Confidence: {src.confidence:.2f})"
        return result

    # Fallback
    return str(raw)


def format_sources(
    sources: list,
    fmt: str = "plain",
    include_confidence: bool = True,
) -> str:
    """
    Format a list of source dicts (as returned by RAGPipeline.query)
    into a human-readable block.

    Args:
        sources       : List of source dicts from RAG response.
        fmt           : Output format — "plain", "markdown", or "apa".
        include_confidence : Show confidence scores.

    Returns:
        Multi-line formatted string suitable for display.
    """
    if not sources:
        return ""

    lines = []
    for src in sources:
        doc_id = src.get("doc_id", "")
        doc_type = src.get("doc_type", "UU")
        year = src.get("year", "")
        score = src.get("score", 0.0)

        # Try to parse doc_id as a full citation string first
        parsed = _parse_raw(doc_id) if doc_id else None
        if parsed:
            cs = CitationSource(
                doc_type=parsed.doc_type or doc_type,
                number=parsed.number,
                year=parsed.year or year,
                title=parsed.title,
                confidence=score,
                doc_id=doc_id,
            )
        else:
            # Fallback: extract number from TYPE-NUM-YEAR pattern in doc_id
            number = "?"
            if doc_id:
                # e.g. "UU-13-2008" or "Permenkumham-5-2019"
                segments = doc_id.split("-")
                if len(segments) >= 2:
                    number = segments[1]  # second segment is the number
            cs = CitationSource(
                doc_type=doc_type,
                number=number,
                year=year,
                title="",
                confidence=score,
                doc_id=doc_id,
            )
        lines.append(format_citation(cs, fmt=fmt, include_confidence=include_confidence))

    if fmt == "markdown":
        return "\n".join(f"- {line}" for line in lines)
    return "\n".join(f"  {i+1}. {line}" for i, line in enumerate(lines))


def parse_citation(raw: str) -> CitationSource:
    """
    Parse a raw citation string into a CitationSource dataclass.

    Returns a CitationSource with whatever fields could be extracted;
    unmatched fields remain empty strings.
    """
    return _parse_raw(raw) or CitationSource(
        doc_type="?", number="?", year="?", title=raw
    )


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        "UU 13/2008 tentang Rencana Induk Nasional (IndoGovRAG)",
        "PP 5/2021 tentang Penyelenggaraan Perizinan Berusaha",
        "Perpres 63/2019 tentang Kewarganegaraan",
        "Permenkumham 5/2019",
        "UU 11/2008 Pasal 27 ayat (1)",
        "Perda 10/2016 tentang Pajak Daerah",
    ]

    print("=" * 70)
    print("Indonesian Legal Citation Formatter — Self-Test")
    print("=" * 70)

    for raw in test_cases:
        src = parse_citation(raw)
        print(f"\n[INPUT]  {raw}")
        print(f"[PLAIN]   {format_citation(src, fmt='plain')}")
        print(f"[MARKDOWN]\n{format_citation(src, fmt='markdown')}")
        print(f"[APA]     {format_citation(src, fmt='apa')}")

    # Test format_sources with mock RAG sources
    print("\n" + "=" * 70)
    print("format_sources() demo")
    print("=" * 70)

    mock_sources = [
        {"doc_id": "UU-13-2008", "doc_type": "UU", "year": "2008", "score": 0.92},
        {"doc_id": "PP-24-2018", "doc_type": "PP", "year": "2018", "score": 0.88},
    ]

    print("\n[PLAIN]")
    print(format_sources(mock_sources, fmt="plain"))
    print("\n[MARKDOWN]")
    print(format_sources(mock_sources, fmt="markdown"))
