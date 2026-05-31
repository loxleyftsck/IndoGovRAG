"""IndoGovRAG legal utilities package."""

__all__ = []

# Deadline Calculator (always available)
from .deadline_calculator import (
    calculate_business_days,
    is_business_day,
    get_next_business_day,
    add_business_days,
    get_deadline_remaining,
    get_holidays,
    format_deadline_report,
    DeadlineResult,
    compute_deadline,
)
__all__.extend([
    "calculate_business_days",
    "is_business_day",
    "get_next_business_day",
    "add_business_days",
    "get_deadline_remaining",
    "get_holidays",
    "format_deadline_report",
    "DeadlineResult",
    "compute_deadline",
])

# Citation Formatter (if available)
try:
    from .citation_formatter import (
        CitationSource,
        DocType,
        format_citation,
        format_sources,
        parse_citation,
    )
    __all__.extend([
        "CitationSource",
        "DocType",
        "format_citation",
        "format_sources",
        "parse_citation",
    ])
except ImportError:
    pass

# Legal Q&A (if available)
try:
    from .legal_qa import LegalQA, LegalQAResult, ask_legal
    __all__.extend(["LegalQA", "LegalQAResult", "ask_legal"])
except ImportError:
    pass

# Amendment Tracker (if available)
try:
    from .amendment_tracker import (
        AmendmentTracker,
        get_tracker,
        track_amendment,
        get_amendment_history,
        check_if_amended,
        get_latest_version,
        find_related_amendments,
        format_amendment_report,
    )
    __all__.extend([
        "AmendmentTracker",
        "get_tracker",
        "track_amendment",
        "get_amendment_history",
        "check_if_amended",
        "get_latest_version",
        "find_related_amendments",
        "format_amendment_report",
    ])
except ImportError:
    pass

# Clause-Level Chunking (if available)
try:
    from .clause_chunking import (
        LegalClauseChunker,
        ClauseChunk,
        ClauseType,
        extract_clauses,
        extract_article_metadata,
        validate_clause_structure,
        detect_clause_type,
        BAB_PATTERN,
        PASAL_PATTERN,
        AYAT_PATTERN,
        BAGIAN_PATTERN,
        PARAGRAF_PATTERN,
        ARTICLE_TYPE_KEYWORDS,
    )
    __all__.extend([
        "LegalClauseChunker",
        "ClauseChunk",
        "ClauseType",
        "extract_clauses",
        "extract_article_metadata",
        "validate_clause_structure",
        "detect_clause_type",
        "BAB_PATTERN",
        "PASAL_PATTERN",
        "AYAT_PATTERN",
        "BAGIAN_PATTERN",
        "PARAGRAF_PATTERN",
        "ARTICLE_TYPE_KEYWORDS",
    ])
except ImportError:
    pass

# Document Analyzer (if available)
try:
    from .document_analyzer import (
        LegalDocumentAnalyzer,
        create_analyzer,
        DocumentAnalysisResult,
        ClauseResult,
        AnalysisSummary,
        CLAUSE_TYPES,
        LEGAL_REFERENCES,
        RISK_PATTERNS,
        SAMPLE_CONTRACT,
        run_demo as run_demo_analyzer,
    )
    __all__.extend([
        "LegalDocumentAnalyzer",
        "create_analyzer",
        "DocumentAnalysisResult",
        "ClauseResult",
        "AnalysisSummary",
        "CLAUSE_TYPES",
        "LEGAL_REFERENCES",
        "RISK_PATTERNS",
        "SAMPLE_CONTRACT",
        "run_demo_analyzer",
    ])
except ImportError:
    pass
