"""
Version Tracking Configuration
Tracks all component versions for reproducibility and explainability
"""

from datetime import datetime

# === SYSTEM METADATA ===
SYSTEM_VERSION = "1.0.0-enterprise"
DEPLOYMENT_DATE = "2026-01-11"
LAST_UPDATED = datetime.now().isoformat()

# === COMPONENT VERSIONS ===
VERSIONS = {
    # Core system
    "system": SYSTEM_VERSION,
    "deployment_date": DEPLOYMENT_DATE,
    
    # Data pipeline
    "chunking_strategy": "recursive-512-overlap-50-v1.0",
    "chunk_size": 512,
    "chunk_overlap": 50,
    
    # Embedding
    "embedding_model": "sentence-transformers/multilingual-e5-base",
    "embedding_version": "v1.0",
    "embedding_dimensions": 768,
    
    # Vector database
    "vector_db": "chromadb",
    "vector_db_version": "0.4.18",
    "distance_metric": "cosine",
    
    # Retrieval
    "retrieval_method": "hybrid",
    "retrieval_alpha": 0.5,  # Vector vs BM25 weight
    "retrieval_top_k": 5,
    "reranker": None,  # Not implemented yet
    
    # LLM
    "llm_provider": "google-gemini",
    "llm_model": "gemini-1.5-flash",
    "llm_temperature": 0.7,
    "llm_max_tokens": 512,
    
    # Prompts
    "prompt_template_version": "v2.1",
    "system_prompt_hash": "sha256:a1b2c3...",  # Hash for verification
    
    # Safety
    "toxicity_filter": "detoxify-v0.5",
    "toxicity_threshold": 0.7,
    "evidence_grounding_version": "threshold-0.5-v1.0",
    "evidence_min_score": 0.5,
    
    # Observability
    "tracing_backend": "jaeger",
    "metrics_backend": "prometheus",
    "logging_format": "structured-json"
}

# === VERSION CHANGELOG ===
VERSION_CHANGELOG = {
    "1.0.0-enterprise": {
        "date": "2026-01-11",
        "changes": [
            "Added feedback API",
            "Implemented audit trail",
            "Added version explainability",
            "GDPR compliance features"
        ]
    },
    "1.0.0-beta": {
        "date": "2026-01-10",
        "changes": [
            "Canary deployment",
            "Toxicity filtering",
            "Evidence grounding"
        ]
    },
    "1.0.0-alpha": {
        "date": "2026-01-06",
        "changes": [
            "OpenTelemetry tracing",
            "Prometheus metrics",
            "Grafana dashboards"
        ]
    }
}


def get_version_info() -> dict:
    """
    Get all version info for response metadata
    
    Returns dict with:
    - system_version
    - last_updated
    - components (all component versions)
    """
    return {
        "system_version": SYSTEM_VERSION,
        "deployment_date": DEPLOYMENT_DATE,
        "last_updated": LAST_UPDATED,
        "components": VERSIONS
    }


def get_user_friendly_versions() -> dict:
    """
    Get user-friendly version info (less technical)
    For inclusion in query responses
    """
    return {
        "system": SYSTEM_VERSION,
        "data_updated": DEPLOYMENT_DATE,
        "ai_model": f"{VERSIONS['llm_provider']}/{VERSIONS['llm_model']}",
        "search_method": VERSIONS['retrieval_method'],
        "safety_features": ["toxicity_filter", "evidence_check"]
    }


def get_source_version(doc_id: str) -> dict:
    """
    Get version info for a specific source document
    In production, query document metadata
    """
    # Placeholder - would query actual document DB
    return {
        "doc_id": doc_id,
        "version": "v1.0",
        "last_updated": "2026-01-01",
        "source": "manual_collection"
    }
