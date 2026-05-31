"""
Clause-Level Chunking for Indonesian Legal Documents.

Provides structured parsing and chunking of Indonesian regulations (UU, Perpres,
PP, Perda, dll.) at the clause level (BAB, Pasal, Ayat) for precise legal
retrieval in RAG pipelines.

Features:
- Parse Indonesian legal document structure
- Extract clause metadata (BAB, Pasal, Ayat)
- Semantic chunking per clause
- Integration with existing Chunk dataclass
- Clause type classification (definitions, rights, obligations, dll.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# =============================================================================
# REGEX PATTERNS — Indonesian Legal Documents
# =============================================================================

# BAB (Chapter): BAB I, BAB II, BAB III, BAB 1, BAB 2, dll.
BAB_PATTERN = re.compile(
    r'^(BAB\s+[IVXLCDM]+|[Bb][Aa][Bb]\s*\.\s*\d+|[Bb][Aa][Bb]\s+\d+)',
    re.MULTILINE | re.IGNORECASE
)

# Pasal identifier — matches "Pasal 1", "Pasal 1A", "Pasal 1 (2)", "Pasal-pasal 3"
PASAL_PATTERN = re.compile(
    r'(?:Pasal-pasal\s+|Pasal\s+)(\d+[A-Z]?)(?:\s*\(\s*(\d+)\s*\))?',
    re.IGNORECASE
)

# Ayat within a clause — matches "ayat (1)", "ayat(2)", "ayat 3", "(1)", "(2)" inline
AYAT_PATTERN = re.compile(
    r'(?:^|\n)(?:(?:ayat|ayat-ayat)\s*\(?\s*(\d+)\s*\)?)|'
    r'(?<=\n|\()(\d+)(?=\s*[.)])',
    re.IGNORECASE | re.MULTILINE
)

# Bagian (Section within BAB)
BAGIAN_PATTERN = re.compile(
    r'(?:^|\n)(?:(?:Bagian\s+)([IVXLCDM]+|\d+))',
    re.MULTILINE | re.IGNORECASE
)

# Paragraf marker
PARAGRAF_PATTERN = re.compile(
    r'^(?:Paragraf\s+)([IVXLCDM]+|\d+)',
    re.MULTILINE | re.IGNORECASE
)

# Article structural keywords (for clause type classification)
ARTICLE_TYPE_KEYWORDS: Dict[str, List[str]] = {
    'definitions': [
        'yang dimaksud dengan', 'yang selanjutnya disebut', 'adalah', 'selanjutnya',
        'berarti', 'sebagaimana dimaksud', 'yang dimaksudkan'
    ],
    'rights': [
        'berhak', 'mempunyai hak', 'hak untuk', 'dapat memperoleh', '有权',
        'memiliki hak', 'diberikan hak', 'menikmati'
    ],
    'obligations': [
        'wajib', 'harus', 'tidak boleh', 'dilarang', 'kewajiban', 'tanggung jawab',
        'bertanggung jawab', 'seharusnya', 'haruslah'
    ],
    'prohibitions': [
        'dilarang', 'tidak boleh', 'dilarang keras', 'diperbolehkan',
        'dilarang dengan alasan', 'tidak diizinkan'
    ],
    'procedures': [
        'prosedur', 'mekanisme', 'tata cara', 'cara', 'langkah-langkah',
        'dilakukan dengan', 'dilaksanakan dengan'
    ],
    'sanctions': [
        'sanksi', 'pidana', 'denda', 'hukuman', 'pidana kurungan', 'pidana penjara',
        'denda administratif', 'pengenaan sanksi'
    ],
    'definitions_list': [
        'yang dimaksud dengan', 'adalah', 'selanjutnya'
    ],
}

# Clause type titles (commonly appear in Indonesian regulations)
CLAUSE_TYPE_TITLES: Dict[str, List[str]] = {
    'ketentuan_umum': ['ketentuan umum', 'ketentuan umum (umum)', 'umum'],
    'hak_dan_kewajiban': ['hak dan kewajiban', 'hak, kewajiban', 'hak& kewajiban'],
    'ketentuan_peralihan': ['ketentuan peralihan', 'pasal penjelas', 'penutup'],
    'ketentuan_lain': ['ketentuan lain', 'lain-lain', 'sanksi'],
    'bagian_umum': ['bagian umum', 'umum'],
}


# =============================================================================
# CLAUSE TYPE ENUM
# =============================================================================

class ClauseType(Enum):
    DEFINITIONS = "definitions"
    RIGHTS = "rights"
    OBLIGATIONS = "obligations"
    PROHIBITIONS = "prohibitions"
    PROCEDURES = "procedures"
    SANCTIONS = "sanctions"
    GENERAL = "general"
    TRANSITIONAL = "transitional"
    CLOSING = "closing"
    UNKNOWN = "unknown"


# =============================================================================
# CLAUSE-LEVEL CHUNK DATACLASS
# =============================================================================

@dataclass
class ClauseChunk:
    """
    A single clause-level chunk extracted from a legal document.

    Extends the base Chunk dataclass with legal-specific metadata.
    """
    text: str
    doc_id: str
    chunk_id: int
    start_char: int
    end_char: int
    num_tokens: int
    metadata: Dict = field(default_factory=dict)
    coherence_score: Optional[float] = None

    # Legal-specific fields
    bab: Optional[str] = None          # BAB identifier (e.g., "I", "II")
    pasal: Optional[int] = None        # Pasal number
    ayat: Optional[List[int]] = field(default_factory=list)  # Ayat numbers
    clause_type: ClauseType = ClauseType.UNKNOWN
    title: Optional[str] = None        # Clause title (e.g., "Ketentuan Umum")
    raw_pasal_ref: Optional[str] = None  # Raw Pasal reference string

    def to_dict(self) -> Dict:
        """Serialize to dictionary for storage/serialization."""
        return {
            'text': self.text,
            'doc_id': self.doc_id,
            'chunk_id': self.chunk_id,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'num_tokens': self.num_tokens,
            'metadata': self.metadata,
            'coherence_score': self.coherence_score,
            'bab': self.bab,
            'pasal': self.pasal,
            'ayat': self.ayat,
            'clause_type': self.clause_type.value,
            'title': self.title,
            'raw_pasal_ref': self.raw_pasal_ref,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> ClauseChunk:
        """Deserialize from dictionary."""
        d = dict(d)
        if 'clause_type' in d and isinstance(d['clause_type'], str):
            d['clause_type'] = ClauseType(d['clause_type'])
        return cls(**d)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _count_tokens(text: str) -> int:
    """Estimate token count (1.3 tokens/word for Indonesian)."""
    return int(len(text.split()) * 1.3)


def _roman_to_int(roman: str) -> str:
    """Convert Roman numeral to string representation."""
    roman = roman.upper()
    val = 0
    table = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
    for i in range(len(roman) - 1):
        if table[roman[i]] < table[roman[i + 1]]:
            val -= table[roman[i]]
        else:
            val += table[roman[i]]
    val += table[roman[-1]]
    return str(val)


def _normalize_bab(bab_str: str) -> Optional[str]:
    """Normalize BAB reference to consistent format."""
    if not bab_str:
        return None
    bab_str = bab_str.strip()
    # Extract the identifier portion
    m = re.search(r'[IVXLCDM]+|\d+', bab_str)
    if m:
        val = m.group()
        # If Roman numeral, convert
        if re.match(r'[IVXLCDM]+$', val.upper()):
            return _roman_to_int(val.upper())
        return val
    return None


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs."""
    paragraphs = re.split(r'\n\s*\n+', text)
    return [p.strip() for p in paragraphs if p.strip()]


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


# =============================================================================
# METADATA EXTRACTION
# =============================================================================

def extract_article_metadata(clause_text: str) -> Dict:
    """
    Extract BAB, Pasal, Ayat, and title from a clause text.

    Args:
        clause_text: Raw text of a single clause

    Returns:
        Dictionary with bab, pasal, ayat, title, raw_pasal_ref fields
    """
    result = {
        'bab': None,
        'pasal': None,
        'ayat': [],
        'title': None,
        'raw_pasal_ref': None,
    }

    lines = clause_text.split('\n')
    first_line = lines[0].strip() if lines else ''

    # --- Extract BAB ---
    bab_match = BAB_PATTERN.search(clause_text)
    if bab_match:
        result['bab'] = _normalize_bab(bab_match.group(1) if bab_match.lastindex else bab_match.group())

    # --- Extract Pasal ---
    pasal_match = PASAL_PATTERN.search(first_line)
    if not pasal_match:
        # Try scanning whole clause text
        all_pasal = PASAL_PATTERN.findall(clause_text)
        if all_pasal:
            pasal_match = re.search(PASAL_PATTERN.pattern, first_line)

    if pasal_match:
        result['pasal'] = int(pasal_match.group(1))
        result['raw_pasal_ref'] = f"Pasal {pasal_match.group(1)}"
        if pasal_match.lastindex and pasal_match.group(2):
            result['ayat'] = [int(pasal_match.group(2))]

    # --- Extract all Ayat numbers ---
    ayat_matches = AYAT_PATTERN.findall(clause_text)
    if ayat_matches:
        # findall returns tuples when pattern has multiple groups; flatten
        raw_ayat = []
        for m in ayat_matches:
            if isinstance(m, tuple):
                raw_ayat.extend(int(x) for x in m if x)
            else:
                raw_ayat.append(int(m))
        if not result['ayat']:
            result['ayat'] = sorted(set(raw_ayat))
        else:
            result['ayat'] = sorted(set(result['ayat'] + raw_ayat))

    # --- Extract clause title from first non-empty line after BAB/Pasal ---
    title_candidates = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Stop at number lists (definisi) or ayat markers
        if re.match(r'^\d+\.', stripped) or re.match(r'^ayat', stripped, re.I):
            break
        # Stop if line is too long (content, not a title)
        if len(stripped) > 120:
            break
        # Skip lines that look like section headers like "Bagian 1" or "Paragraf I"
        if BAGIAN_PATTERN.match(stripped) or PARAGRAF_PATTERN.match(stripped):
            break
        title_candidates.append(stripped)

    if title_candidates:
        # Take the first short line as the title
        result['title'] = title_candidates[0]

    return result


def detect_clause_type(clause_text: str) -> ClauseType:
    """
    Classify the type of a legal clause based on its content.

    Only examines the first N characters of the clause body (after the header)
    to avoid false signals from explanatory text deep inside the clause.

    Args:
        clause_text: Full text of the clause

    Returns:
        ClauseType enum value
    """
    # Check first line of clause header
    first_line = clause_text.split('\n')[0].lower().strip()
    for ctype, titles in CLAUSE_TYPE_TITLES.items():
        for title in titles:
            if title in first_line:
                if ctype == 'ketentuan_umum':
                    return ClauseType.DEFINITIONS
                elif ctype in ('ketentuan_peralihan', 'ketentuan_lain'):
                    return ClauseType.TRANSITIONAL
                elif ctype == 'hak_dan_kewajiban':
                    return ClauseType.RIGHTS

    # Score each type based on keyword matches in the first 400 chars
    # (avoid signals from deep explanatory text)
    search_window = clause_text[:400].lower()

    scores: Dict[ClauseType, float] = {ct: 0.0 for ct in ClauseType}

    for ctype_str, keywords in ARTICLE_TYPE_KEYWORDS.items():
        try:
            ctype = ClauseType(ctype_str)
        except ValueError:
            continue
        for kw in keywords:
            if kw.lower() in search_window:
                scores[ctype] += 1.0

    # Check for definitions list pattern: numbered items after header
    # (look for "1. " / "2. " style lists anywhere in clause)
    if re.search(r'^\d+\.\s+\w', clause_text, re.MULTILINE):
        # Only accept DEFINITIONS if "yang dimaksud" or "adalah" appears near start
        if re.search(r'(yang\s+d[iy]maksud|adalah|selanjutnya)', search_window):
            return ClauseType.DEFINITIONS

    # Return highest scoring type (if any score > 0)
    best = max(scores, key=lambda k: scores[k])
    if scores[best] > 0:
        return best

    return ClauseType.UNKNOWN


def validate_clause_structure(clause_text: str) -> Dict:
    """
    Validate the structural completeness of a clause.

    Args:
        clause_text: Text of the clause to validate

    Returns:
        Dictionary with:
            - is_valid: bool
            - issues: List[str] of issue descriptions
            - completeness_score: float 0-1
    """
    issues: List[str] = []
    score = 1.0

    lines = [l.strip() for l in clause_text.split('\n') if l.strip()]

    if not lines:
        issues.append("Clause is empty")
        return {'is_valid': False, 'issues': issues, 'completeness_score': 0.0}

    first_line = lines[0]

    # Check for Pasal header
    if not PASAL_PATTERN.search(first_line):
        issues.append("Missing Pasal header")
        score -= 0.3

    # Check for content
    content_lines = [l for l in lines[1:] if not BAGIAN_PATTERN.match(l) and not PARAGRAF_PATTERN.match(l)]
    if not content_lines:
        issues.append("No content after header")
        score -= 0.2

    # Check for very short clauses
    if len(clause_text) < 30:
        issues.append("Clause text is very short")
        score -= 0.2

    # Check for orphaned ayat (number without content)
    for line in lines:
        ayat_m = AYAT_PATTERN.search(line)
        if ayat_m and len(line.strip()) < 15:
            issues.append(f"Ayat ({ayat_m.group(1)}) may lack content")
            score -= 0.1

    # Check BAB consistency
    bab_matches = BAB_PATTERN.findall(clause_text)
    if len(bab_matches) > 1:
        issues.append("Multiple BAB markers in single clause")
        score -= 0.1

    score = max(0.0, min(1.0, score))
    return {
        'is_valid': score >= 0.7,
        'issues': issues,
        'completeness_score': score,
    }


# =============================================================================
# CLAUSE EXTRACTION
# =============================================================================

def extract_clauses(text: str) -> List[Dict]:
    """
    Extract individual clauses from a legal document text.

    Parses the document into clause blocks, each containing:
      - text: raw clause text
      - bab: BAB identifier
      - pasal: Pasal number
      - ayat: list of Ayat numbers
      - title: clause title
      - clause_type: ClauseType enum value

    Args:
        text: Full legal document text

    Returns:
        List of clause dictionaries
    """
    clauses: List[Dict] = []
    lines = text.split('\n')

    current_bab: Optional[str] = None
    current_clauses_lines: List[str] = []
    current_pasal: Optional[int] = None
    pending_ayat: List[int] = []

    def _flush_clause(lines_list: List[str], bab: Optional[str], pasal: Optional[int]) -> Optional[Dict]:
        if not lines_list:
            return None
        text_block = '\n'.join(lines_list).strip()
        if not text_block:
            return None
        meta = extract_article_metadata(text_block)
        return {
            'text': text_block,
            'bab': bab or meta.get('bab'),
            'pasal': pasal or meta.get('pasal'),
            'ayat': meta.get('ayat', []),
            'title': meta.get('title'),
            'raw_pasal_ref': meta.get('raw_pasal_ref'),
            'clause_type': detect_clause_type(text_block),
        }

    for line in lines:
        stripped = line.strip()

        # --- Track BAB ---
        bab_match = BAB_PATTERN.match(stripped)
        if bab_match:
            # Flush current clause before new BAB
            if current_clauses_lines:
                clause = _flush_clause(current_clauses_lines, current_bab, current_pasal)
                if clause:
                    clauses.append(clause)
                current_clauses_lines = []
                current_pasal = None
            current_bab = _normalize_bab(bab_match.group())

        # --- Track Bagian / Paragraf (may reset context) ---
        if BAGIAN_PATTERN.match(stripped) or PARAGRAF_PATTERN.match(stripped):
            if current_clauses_lines:
                clause = _flush_clause(current_clauses_lines, current_bab, current_pasal)
                if clause:
                    clauses.append(clause)
                current_clauses_lines = []
                current_pasal = None

        # --- Detect new Pasal ---
        pasal_match = PASAL_PATTERN.match(stripped)
        if pasal_match:
            # Flush previous clause
            if current_clauses_lines:
                clause = _flush_clause(current_clauses_lines, current_bab, current_pasal)
                if clause:
                    clauses.append(clause)
                current_clauses_lines = []

            current_pasal = int(pasal_match.group(1))
            current_clauses_lines = [stripped]
            continue

        # --- Otherwise accumulate lines into current clause ---
        if current_clauses_lines or (stripped and current_pasal is not None):
            current_clauses_lines.append(stripped)

    # Flush final clause
    if current_clauses_lines:
        clause = _flush_clause(current_clauses_lines, current_bab, current_pasal)
        if clause:
            clauses.append(clause)

    return clauses


# =============================================================================
# MAIN CHUNKER CLASS
# =============================================================================

class LegalClauseChunker:
    """
    Clause-level chunker for Indonesian legal documents.

    Provides structured parsing of Indonesian regulations (UU, Perpres, PP, Perda)
    at the clause level, with semantic classification and full metadata.

    Inherits from / extends the existing Chunk-based pipeline while adding
    legal-specific metadata (BAB, Pasal, Ayat, clause_type).

    Example:
        from src.legal.clause_chunking import LegalClauseChunker

        chunker = LegalClauseChunker()
        chunks = chunker.parse_legal_document(text, doc_id="UU_13_2008")

        for chunk in chunks:
            print(chunk.metadata['pasal'], chunk.metadata['clause_type'])
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 64,
        min_chunk_size: int = 50,
        include_bab_context: bool = True,
    ):
        """
        Initialize the LegalClauseChunker.

        Args:
            chunk_size: Target tokens per chunk (fallback for oversized clauses)
            overlap: Token overlap between chunks
            min_chunk_size: Minimum chunk size threshold
            include_bab_context: If True, prepend BAB context to each clause chunk
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.include_bab_context = include_bab_context

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def parse_legal_document(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict] = None,
    ) -> List[ClauseChunk]:
        """
        Parse a full legal document into clause-level chunks.

        This is the main entry point. It:
          1. Extracts individual clauses (BAB / Pasal / Ayat)
          2. Classifies each clause type
          3. Validates structure
          4. Falls back to semantic chunking for oversized clauses
          5. Returns ClauseChunk objects with full metadata

        Args:
            text: Full legal document text
            doc_id: Document identifier
            metadata: Optional document-level metadata

        Returns:
            List of ClauseChunk objects
        """
        if not metadata:
            metadata = {}

        raw_clauses = extract_clauses(text)
        chunks: List[ClauseChunk] = []
        chunk_id = 0

        for clause in raw_clauses:
            clause_text = clause['text']
            tokens = _count_tokens(clause_text)

            # If clause fits within chunk_size, emit as-is
            if tokens <= self.chunk_size:
                chunk = self._make_clause_chunk(
                    clause_text=clause_text,
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    bab=clause.get('bab'),
                    pasal=clause.get('pasal'),
                    ayat=clause.get('ayat', []),
                    title=clause.get('title'),
                    raw_pasal_ref=clause.get('raw_pasal_ref'),
                    clause_type=clause.get('clause_type', ClauseType.UNKNOWN),
                    doc_metadata=metadata,
                    start_char=text.find(clause_text),
                    end_char=text.find(clause_text) + len(clause_text),
                )
                chunks.append(chunk)
                chunk_id += 1
                continue

            # Oversized clause — split semantically
            sub_chunks = self._split_clause(
                clause_text=clause_text,
                doc_id=doc_id,
                start_chunk_id=chunk_id,
                bab=clause.get('bab'),
                pasal=clause.get('pasal'),
                ayat=clause.get('ayat', []),
                title=clause.get('title'),
                raw_pasal_ref=clause.get('raw_pasal_ref'),
                clause_type=clause.get('clause_type', ClauseType.UNKNOWN),
                doc_metadata=metadata,
            )
            chunks.extend(sub_chunks)
            chunk_id += len(sub_chunks)

        # Calculate coherence scores
        for chunk in chunks:
            chunk.coherence_score = self._calculate_coherence(chunk)

        return chunks

    def chunk_by_clause(
        self,
        document: str,
        doc_id: str,
        overlap: int = 0,
        metadata: Optional[Dict] = None,
    ) -> List[ClauseChunk]:
        """
        Chunk a document strictly by clause boundaries.

        Args:
            document: Full document text
            doc_id: Document identifier
            overlap: Reserved (clause-level chunking uses structural boundaries)
            metadata: Optional document-level metadata

        Returns:
            List of ClauseChunk objects
        """
        return self.parse_legal_document(document, doc_id, metadata)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _make_clause_chunk(
        self,
        clause_text: str,
        doc_id: str,
        chunk_id: int,
        bab: Optional[str],
        pasal: Optional[int],
        ayat: List[int],
        title: Optional[str],
        raw_pasal_ref: Optional[str],
        clause_type: ClauseType,
        doc_metadata: Dict,
        start_char: int,
        end_char: int,
    ) -> ClauseChunk:
        """Construct a ClauseChunk object."""
        text = clause_text
        if self.include_bab_context and bab:
            text = f"BAB {bab}\n{clause_text}"

        tokens = _count_tokens(text)

        # Build metadata dict (legal fields + base fields)
        chunk_metadata = {
            **doc_metadata,
            'type': clause_type.value,
            'bab': bab,
            'pasal': pasal,
            'ayat': ayat,
            'clause_type': clause_type.value,
            'title': title,
            'raw_pasal_ref': raw_pasal_ref,
            'has_list': bool(re.search(r'^\s*[\d\-\•]\s+', text, re.MULTILINE)),
            'has_numbers': bool(re.search(r'\d+', text)),
        }

        return ClauseChunk(
            text=text,
            doc_id=doc_id,
            chunk_id=chunk_id,
            start_char=start_char,
            end_char=end_char,
            num_tokens=tokens,
            metadata=chunk_metadata,
            bab=bab,
            pasal=pasal,
            ayat=ayat,
            clause_type=clause_type,
            title=title,
            raw_pasal_ref=raw_pasal_ref,
        )

    def _split_clause(
        self,
        clause_text: str,
        doc_id: str,
        start_chunk_id: int,
        bab: Optional[str],
        pasal: Optional[int],
        ayat: List[int],
        title: Optional[str],
        raw_pasal_ref: Optional[str],
        clause_type: ClauseType,
        doc_metadata: Dict,
    ) -> List[ClauseChunk]:
        """Split an oversized clause into smaller semantic sub-chunks."""
        paragraphs = _split_paragraphs(clause_text)
        chunks: List[ClauseChunk] = []
        current_parts: List[str] = []
        current_tokens = 0
        offset = 0
        sub_id = 0

        for para in paragraphs:
            para_tokens = _count_tokens(para)

            if current_tokens + para_tokens <= self.chunk_size:
                current_parts.append(para)
                current_tokens += para_tokens
            else:
                if current_parts:
                    sub_text = '\n\n'.join(current_parts)
                    start = clause_text.find(sub_text)
                    end = start + len(sub_text)
                    chunks.append(self._make_clause_chunk(
                        clause_text=sub_text,
                        doc_id=doc_id,
                        chunk_id=start_chunk_id + sub_id,
                        bab=bab,
                        pasal=pasal,
                        ayat=ayat,
                        title=title,
                        raw_pasal_ref=raw_pasal_ref,
                        clause_type=clause_type,
                        doc_metadata=doc_metadata,
                        start_char=start,
                        end_char=end,
                    ))
                    sub_id += 1
                    current_parts = []
                    current_tokens = 0

                if para_tokens > self.chunk_size:
                    # Split at sentence level
                    sentences = _split_sentences(para)
                    for sent in sentences:
                        sent_tokens = _count_tokens(sent)
                        if current_tokens + sent_tokens <= self.chunk_size:
                            current_parts.append(sent)
                            current_tokens += sent_tokens
                        else:
                            if current_parts:
                                sub_text = ' '.join(current_parts)
                                start = clause_text.find(sub_text)
                                end = start + len(sub_text)
                                chunks.append(self._make_clause_chunk(
                                    clause_text=sub_text,
                                    doc_id=doc_id,
                                    chunk_id=start_chunk_id + sub_id,
                                    bab=bab,
                                    pasal=pasal,
                                    ayat=ayat,
                                    title=title,
                                    raw_pasal_ref=raw_pasal_ref,
                                    clause_type=clause_type,
                                    doc_metadata=doc_metadata,
                                    start_char=start,
                                    end_char=end,
                                ))
                                sub_id += 1
                                current_parts = []
                                current_tokens = 0
                            current_parts.append(sent)
                            current_tokens = sent_tokens
                else:
                    current_parts.append(para)
                    current_tokens = para_tokens

        # Final sub-chunk
        if current_parts:
            sub_text = '\n\n'.join(current_parts)
            start = clause_text.find(sub_text)
            end = start + len(sub_text) if start != -1 else 0
            chunks.append(self._make_clause_chunk(
                clause_text=sub_text,
                doc_id=doc_id,
                chunk_id=start_chunk_id + sub_id,
                bab=bab,
                pasal=pasal,
                ayat=ayat,
                title=title,
                raw_pasal_ref=raw_pasal_ref,
                clause_type=clause_type,
                doc_metadata=doc_metadata,
                start_char=start,
                end_char=end,
            ))

        return chunks

    def _calculate_coherence(self, chunk: ClauseChunk) -> float:
        """Calculate coherence score (0-1) for a clause chunk."""
        text = chunk.text
        score = 1.0

        if text and text[0].islower():
            score -= 0.2
        if text and text[-1] not in '.!?':
            score -= 0.2
        if chunk.title:
            score += 0.1
        if chunk.num_tokens < self.min_chunk_size:
            score -= 0.3

        return max(0.0, min(1.0, score))


# =============================================================================
# DEMO / TEST
# =============================================================================

def demo_clause_chunker():
    """Demo clause-level chunking with a sample Indonesian regulation."""

    print("[TEST] Clause-Level Legal Chunking Demo\n")

    sample_doc = """
PERATURAN PRESIDEN REPUBLIK INDONESIA
NOMOR 26 TAHUN 2009

TENTANG PENERAPAN KARTU TANDA PENDUDUK BERBASIS NOMOR INDUK KEPENDUDUKAN SECARA NASIONAL

BAB I
KETENTUAN UMUM

Pasal 1
Dalam Peraturan Presiden ini, yang dimaksud dengan:

1. Kartu Tanda Penduduk, yang selanjutnya disingkat KTP adalah identitas resmi
   penduduk sebagai bukti diri yang diterbitkan oleh Instansi Pelaksana yang
   berlaku di seluruh wilayah Negara Kesatuan Republik Indonesia.

2. Nomor Induk Kependudukan, yang selanjutnya disingkat NIK adalah nomor identitas
   penduduk yang bersifat unik atau khas, tunggal dan melekat pada seseorang yang
   terdaftar sebagai Penduduk Indonesia.

3. Database Kependudukan adalah kumpulan data yang tersimpan secara sistematis dan
   dapat diakses melalui sistem aplikasi tertentu.

BAB II
PENERAPAN KTP BERBASIS NIK

Pasal 2
(1) Setiap Penduduk yang telah berumur 17 tahun atau telah kawin atau pernah kawin
    wajib memiliki KTP.

(2) KTP sebagaimana dimaksud pada ayat (1) berlaku sebagai identitas yang sah untuk
    mendapatkan pelayanan publik.

(3) KTP berbasis NIK sebagaimana dimaksud pada ayat (1) diterbitkan oleh Pemerintah
    Kabupaten/Kota.

Pasal 3
(1) Setiap Penduduk sebagaimana dimaksud dalam Pasal 2 berhak mendapatkan
    pelayanan publik secara efisien dan mudah.

(2) Pemerintah Kabupaten/Kota wajib menerbitkan KTP dalam jangka waktu paling
    lama 14 hari kerja sejak pendaftaran.

Pasal 4
(1) Instansi Pelaksana dilarang memungut biaya apapun untuk penerbitan KTP.

(2) Pelanggaran terhadap ketentuan sebagaimana dimaksud pada ayat (1) dikenakan
    sanksi administratif sesuai ketentuan peraturan perundang-undangan.

BAB III
KETENTUAN PERALIHAN

Pasal 5
KTP yang telah diterbitkan sebelum berlakunya Peraturan Presiden ini tetap berlaku
sampai dengan masa berlakunya berakhir atau diterbitkan KTP baru.
"""

    chunker = LegalClauseChunker(
        chunk_size=512,
        overlap=64,
        min_chunk_size=50,
        include_bab_context=True,
    )

    chunks = chunker.parse_legal_document(
        text=sample_doc,
        doc_id="Perpres_26_2009",
        metadata={
            'doc_type': 'Perpres',
            'number': '26',
            'year': '2009',
            'category': 'civil_administration',
        },
    )

    print(f"[STAT] Chunking Results")
    print("=" * 70)
    print(f"Total Chunks     : {len(chunks)}")
    avg_tokens = sum(c.num_tokens for c in chunks) / len(chunks) if chunks else 0
    avg_coh = sum(c.coherence_score or 0 for c in chunks) / len(chunks) if chunks else 0
    print(f"Avg Tokens/Chunk : {avg_tokens:.1f}")
    print(f"Avg Coherence    : {avg_coh:.2f}")

    print(f"\n[MSG] Clause Chunks:")
    print("=" * 70)
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {chunk.chunk_id} ---")
        print(f"  BAB     : {chunk.bab}")
        print(f"  Pasal   : {chunk.pasal}")
        print(f"  Ayat    : {chunk.ayat}")
        print(f"  Type    : {chunk.clause_type.value}")
        print(f"  Title   : {chunk.title}")
        print(f"  Tokens  : {chunk.num_tokens}")
        print(f"  Coherence: {chunk.coherence_score:.2f}")
        print(f"  Text    :\n{chunk.text[:300]}")

    # --- Test extract_clauses standalone ---
    print("\n\n[TEST] Standalone extract_clauses()")
    print("=" * 70)
    raw_clauses = extract_clauses(sample_doc)
    for i, c in enumerate(raw_clauses):
        print(f"\nClause {i}: BAB={c['bab']} Pasal={c['pasal']} Ayat={c['ayat']}")
        print(f"  Type: {c['clause_type'].value}")
        print(f"  Title: {c['title']}")
        print(f"  Preview: {c['text'][:120]}...")

    # --- Test extract_article_metadata ---
    print("\n\n[TEST] extract_article_metadata()")
    print("=" * 70)
    meta = extract_article_metadata(
        "Pasal 2\n(1) Setiap Penduduk wajib memiliki KTP.\n(2) KTP berlaku sebagai identitas."
    )
    print(f"Metadata: {meta}")

    # --- Test validate_clause_structure ---
    print("\n\n[TEST] validate_clause_structure()")
    print("=" * 70)
    validation = validate_clause_structure(
        "Pasal 1\nDalam Peraturan Presiden ini, yang dimaksud dengan:\n1. KTP adalah identitas resmi."
    )
    print(f"Validation: {validation}")

    print("\n[OK] Demo complete!")


if __name__ == "__main__":
    demo_clause_chunker()
