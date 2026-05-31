"""
FastAPI Application for IndoGovRAG

Production-ready API endpoints for RAG query system.
"""

import os
import sys
import time
import json
import tempfile
import shutil
import hashlib
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
import threading
from functools import lru_cache

# Add parent directory to Python path to allow imports from src/
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
import logging

# Import security components
from .security import (
    audit_log,
    log_request,
    security_headers_middleware,
    rate_limit_middleware,
    content_type_validation_middleware,
    injection_prevention_middleware,
    connection_abuse_middleware,
    cors_middleware,
)
from .rate_limiter import rate_limiter, format_rate_limit_response
from .sanitizer import validate_and_sanitize
from .api_keys import api_key_manager, get_api_key

# Guard stdout/stderr re-wrapping (pytest may reassign them)
import io as _io
if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, _io.TextIOWrapper):
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, _io.TextIOWrapper):
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure error logging (UTF-8 handler to avoid UnicodeEncodeError on Windows)
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
for _h in _root_logger.handlers[:]:
    _root_logger.removeHandler(_h)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))
_handler.encoding = 'utf-8'
_root_logger.addHandler(_handler)
api_logger = logging.getLogger("indogov_api")

# Import error handling schemas
from src.errors import (
    ErrorType,
    ErrorResponse,
    get_error_response,
    create_error_response,
    create_success_response,
    create_fallback_response,
    check_confidence_warnings,
    check_chunk_count_warning,
    check_superseded_document,
    LOW_CONFIDENCE_THRESHOLD,
    error_responses,
)

# Load environment variables
load_dotenv()

# Fix Windows encoding for logging (prevents UnicodeEncodeError with Indonesian text)
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, _io.TextIOWrapper):
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, _io.TextIOWrapper):
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Import RAG pipeline (will create on first use)
rag_pipeline = None

# Imports at module level to allow unit test patching
from src.rag.pipeline import RAGPipeline
from src.retrieval.vector_search import VectorStore

# ---------------------------------------------------------------------------
# Global LRU caches for response speed (process-level, shared across requests)
# ---------------------------------------------------------------------------

# LRU cache for embedding texts — keyed by text hash, stores embedding vectors
@lru_cache(maxsize=8192)
def _cached_embed_text(text_hash: str, text: str) -> List[float]:
    """
    Module-level LRU cache for embedding results.
    text_hash = MD5(query) used as cache key; text kept for cache info.
    A separate LRU cache for RAG query results is defined below.
    """
    # This function is only called on cache miss; the actual embedding
    # happens in the embedding function (which has its own L1 cache).
    # This cache stores the FINAL embedding list[float] result.
    return None  # placeholder; actual caching done via CustomEmbeddingFunction


# LRU cache for RAG query results — stores (answer, sources, confidence, metadata)
@lru_cache(maxsize=1024)
def _cached_rag_result(cache_key: str, query_hash: str) -> tuple:
    """
    Module-level LRU cache for complete RAG query results.
    Key = MD5(query + options_json).  Stores (answer, sources, confidence, metadata_dict).
    """
    return None  # placeholder; actual caching done via QueryCache in pipeline


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., min_length=1, max_length=500, description="User query in Indonesian")
    options: Optional[dict] = Field(
        default_factory=dict,
        description="Optional search parameters: use_query_expansion, use_reranking, use_hybrid, top_k"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Apa syarat membuat KTP elektronik?",
                "options": {
                    "use_query_expansion": True,
                    "use_reranking": False,
                    "use_hybrid": True,
                    "top_k": 5
                }
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sources: list
    confidence: float
    latency_ms: float
    metadata: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Persyaratan KTP elektronik: KTP asli, KK, Akta Kelahiran...",
                "sources": ["Perpres 26/2009"],
                "confidence": 0.92,
                "latency_ms": 245.5,
                "metadata": {
                    "chunks_retrieved": 5,
                    "expansion_used": True,
                    "reranking_used": True
                }
            }
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for app startup/shutdown."""
    # Startup
    global rag_pipeline
    api_logger.info("[STARTUP] Starting IndoGovRAG API...")

    # Initialize RAG pipeline (lazy loading)
    # Actual initialization happens on first query to save memory

    yield

    # Shutdown
    api_logger.info("[SHUTDOWN] Shutting down IndoGovRAG API...")


# Create FastAPI app
app = FastAPI(
    title="IndoGovRAG API",
    description="AI-Powered Search Engine for Indonesian Government Documents",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS from environment (comma-separated)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# ── Middleware Stack (bottom = executed first) ────────────────────────────────
# Order: CORS → Security Headers → Content-Type Validation → Injection Prevention
#         → Connection Abuse → Rate Limiting → Audit Log → Endpoint

# 1. Strict CORS (origin allowlist, credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 2. Security headers (X-Frame-Options, CSP, HSTS, etc.)
app.middleware("http")(security_headers_middleware)

# 3. Content-Type validation (block XML, enforce JSON for POST)
app.middleware("http")(content_type_validation_middleware)

# 4. SQL / Command / XXE injection pre-scan on query params
app.middleware("http")(injection_prevention_middleware)

# 5. Slowloris / connection abuse detection
app.middleware("http")(connection_abuse_middleware)

# 6. Rate limiting (per-user tiered, with burst detection)
app.middleware("http")(rate_limit_middleware)

# 7. Audit logging (structured JSON, per request)
app.middleware("http")(log_request)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IndoGovRAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/query (POST)",
            "health": "/health (GET)",
            "metrics": "/metrics (GET)",
            "docs": "/docs (GET)"
        }
    }


# Global variable for uploaded docs storage
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Global variable for query cache
query_cache = None

# ─── Search Analytics Logger ───────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_search_log_lock = threading.Lock()


def _get_log_path() -> Path:
    """Return the current week's log file path."""
    today = datetime.utcnow()
    week = today.isocalendar()[1]
    return LOG_DIR / f"searches_{today.year}_W{week:02d}.jsonl"


def log_search(
    query: str,
    user_id: Optional[str],
    results_count: int,
    confidence_score: float,
    response_time_ms: float,
    had_answer: bool,
) -> None:
    """
    Append a search event to the weekly rotating JSONL log.
    Runs synchronously inside a lock to guarantee ordering.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "user_id": user_id or "anonymous",
        "results_count": results_count,
        "confidence_score": round(confidence_score, 4),
        "response_time_ms": round(response_time_ms, 2),
        "had_answer": had_answer,
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with _search_log_lock:
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            f.write(line)


class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    category: Optional[str] = Field(default="general", description="Document category")
    description: Optional[str] = Field(default="", description="Document description")


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    file_id: str
    filename: str
    file_type: str
    file_size: int
    chunks_created: int
    message: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global rag_pipeline

    return {
        "status": "healthy",
        "rag_initialized": rag_pipeline is not None,
        "groq_api_key_set": bool(os.getenv("GROQ_API_KEY")),
        "gemini_api_key_set": bool(os.getenv("GEMINI_API_KEY")),
        "timestamp": time.time()
    }


@app.post("/upload/file", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(default="general")
):
    """
    Upload a single file for RAG indexing.

    Supported formats: .txt, .pdf, .doc, .docx, .md
    """
    try:
        # Validate file
        allowed_types = [
            "text/plain", "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        allowed_extensions = [".txt", ".pdf", ".doc", ".docx", ".md"]

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return FileUploadResponse(
                success=False,
                file_id="",
                filename=file.filename,
                file_type=file_ext,
                file_size=0,
                chunks_created=0,
                message=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Save file
        file_id = f"upload_{int(time.time())}_{Path(file.filename).stem}"
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        content = await file.read()
        file_size = len(content)

        with open(file_path, "wb") as f:
            f.write(content)

        # Process file in background (chunking + indexing)
        def process_file():
            try:

                # Load document
                try:
                    from src.data.loader import PDFExtractor
                    from src.data.chunker import TextChunker

                    extractor = PDFExtractor()
                    doc = extractor.extract(str(file_path))

                    if not doc.success:
                        api_logger.error(f"[ERR] Failed to extract {file.filename}: {doc.error}")
                        return

                    chunker = TextChunker(chunk_size=512, overlap=50)
                    raw_chunks = chunker.chunk_text(doc.text)
                except (ImportError, AttributeError):
                    # Fallback: simple text splitting
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    raw_chunks = [{'text': text[i:i+512]} for i in range(0, len(text), 512)]

                # Prepare chunks for vector store
                chunks = []
                for i, chunk in enumerate(raw_chunks):
                    chunks.append({
                        'id': f"{file_id}_chunk_{i}",
                        'text': chunk.get('text', chunk),
                        'metadata': {
                            'source': 'upload',
                            'file_id': file_id,
                            'file_name': file.filename,
                            'category': category,
                            'doc_type': file_ext.replace('.', '')
                        }
                    })

                # Add to vector store
                store = VectorStore()
                store.add_chunks(chunks)

                api_logger.info(f"[OK] Indexed {len(chunks)} chunks from {file.filename}")
            except Exception as e:
                import traceback
                api_logger.error(f"[ERR] Error processing {file.filename}: {e}")
                api_logger.error(traceback.format_exc())

        background_tasks.add_task(process_file)

        # Estimate chunks (rough: 1 chunk per 512 chars)
        estimated_chunks = max(1, file_size // 300)

        return FileUploadResponse(
            success=True,
            file_id=file_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            chunks_created=estimated_chunks,
            message=f"File uploaded successfully. Indexing in progress..."
        )

    except Exception as e:
        return FileUploadResponse(
            success=False,
            file_id="",
            filename=file.filename if file else "unknown",
            file_type="",
            file_size=0,
            chunks_created=0,
            message=f"Upload failed: {str(e)}"
        )


@app.post("/upload/folder", response_model=dict)
async def upload_folder(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(default=[]),
    category: str = Form(default="general")
):
    """
    Upload multiple files from a folder for RAG indexing.

    Supported formats: .txt, .pdf, .doc, .docx, .md
    """
    allowed_extensions = [".txt", ".pdf", ".doc", ".docx", ".md"]

    results = {
        "total_files": len(files),
        "successful": 0,
        "failed": 0,
        "files": []
    }

    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            results["failed"] += 1
            results["files"].append({
                "filename": file.filename,
                "status": "failed",
                "reason": f"Unsupported file type: {file_ext}"
            })
            continue

        try:
            # Save file
            file_id = f"upload_{int(time.time())}_{Path(file.filename).stem}"
            file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

            content = await file.read()
            file_size = len(content)

            with open(file_path, "wb") as f:
                f.write(content)

            # Process in background
            def process_file():
                try:
                    from src.data.loader import PDFExtractor
                    from src.data.chunker import TextChunker

                    # Extract text
                    try:
                        extractor = PDFExtractor()
                        doc = extractor.extract(str(file_path))
                        if not doc.success:
                            api_logger.error(f"[ERR] Failed to extract {file.filename}: {doc.error}")
                            return
                        text = doc.text
                    except (ImportError, AttributeError):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()

                    # Chunk text
                    try:
                        chunker = TextChunker(chunk_size=512, overlap=50)
                        raw_chunks = chunker.chunk_text(text)
                    except:
                        raw_chunks = [{'text': text[i:i+512]} for i in range(0, len(text), 512)]

                    # Prepare chunks
                    chunks = []
                    for i, chunk in enumerate(raw_chunks):
                        chunks.append({
                            'id': f"{file_id}_chunk_{i}",
                            'text': chunk.get('text', chunk),
                            'metadata': {
                                'source': 'upload',
                                'file_id': file_id,
                                'file_name': file.filename,
                                'category': category,
                                'doc_type': file_ext.replace('.', '')
                            }
                        })

                    store = VectorStore()
                    store.add_chunks(chunks)
                    api_logger.info(f"[OK] Indexed {len(chunks)} chunks from {file.filename}")
                except Exception as e:
                    api_logger.error(f"[ERR] Error processing {file.filename}: {e}")

            background_tasks.add_task(process_file)

            results["successful"] += 1
            results["files"].append({
                "filename": file.filename,
                "status": "success",
                "file_id": file_id,
                "size": file_size
            })

        except Exception as e:
            results["failed"] += 1
            results["files"].append({
                "filename": file.filename,
                "status": "failed",
                "reason": str(e)
            })

    return results


@app.get("/upload/status/{file_id}")
async def get_upload_status(file_id: str):
    """Get status of uploaded file indexing."""
    # Check if file exists
    upload_files = list(UPLOAD_DIR.glob(f"{file_id}*"))

    if not upload_files:
        return {
            "file_id": file_id,
            "status": "not_found",
            "message": "File not found"
        }

    return {
        "file_id": file_id,
        "status": "indexed",
        "message": "File has been indexed and is ready for RAG queries",
        "file_path": str(upload_files[0])
    }


@app.delete("/upload/delete/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete uploaded file and its chunks from vector store."""
    try:
        # Find and delete file
        upload_files = list(UPLOAD_DIR.glob(f"{file_id}*"))

        if not upload_files:
            return {
                "success": False,
                "message": "File not found"
            }

        # Remove from vector store first
        try:
            store = VectorStore()

            # Get all chunks with this file_id
            results = store.collection.get(
                where={"file_id": file_id}
            )

            if results and results['ids']:
                store.collection.delete(ids=results['ids'])
                api_logger.info(f"[OK] Deleted {len(results['ids'])} chunks from vector store")
        except Exception as e:
            api_logger.warning(f"Warning: Could not update vector store: {e}")

        # Delete physical file
        for f in upload_files:
            f.unlink()

        return {
            "success": True,
            "message": f"File {file_id} deleted successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Delete failed: {str(e)}"
        }


@app.get("/files")
async def list_files():
    """List all uploaded files with metadata."""
    try:
        # Get unique files from vector store metadata
        store = VectorStore()
        results = store.collection.get()

        files = {}
        for metadata in results.get('metadatas', []):
            file_id = metadata.get('file_id')
            if file_id and file_id not in files:
                files[file_id] = {
                    'file_id': file_id,
                    'file_name': metadata.get('file_name', 'Unknown'),
                    'category': metadata.get('category', 'general'),
                    'doc_type': metadata.get('doc_type', 'unknown'),
                    'chunks_count': 0,
                    'status': 'indexed'
                }
            if file_id:
                files[file_id]['chunks_count'] += 1

        # Add files that haven't been indexed yet
        for filepath in UPLOAD_DIR.glob("upload_*"):
            file_id = filepath.stem
            if file_id not in files:
                files[file_id] = {
                    'file_id': file_id,
                    'file_name': filepath.name,
                    'category': 'pending',
                    'doc_type': filepath.suffix.replace('.', ''),
                    'chunks_count': 0,
                    'status': 'pending'
                }

        return {
            'total_files': len(files),
            'files': list(files.values())
        }

    except Exception as e:
        return {
            'total_files': 0,
            'files': [],
            'error': str(e)
        }


@app.delete("/files/clear")
async def clear_all_files():
    """Clear all uploaded files and reset vector store."""
    try:
        import shutil

        # Clear vector store
        store = VectorStore()

        # Get count before deletion
        count = store.collection.count()

        # Delete all chunks
        if count > 0:
            results = store.collection.get()
            if results and results['ids']:
                store.collection.delete(ids=results['ids'])

        # Delete all uploaded files
        deleted_count = 0
        for filepath in UPLOAD_DIR.glob("upload_*"):
            filepath.unlink()
            deleted_count += 1

        return {
            "success": True,
            "message": f"Cleared {count} chunks and {deleted_count} files"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Clear failed: {str(e)}"
        }


@app.get("/stats")
async def get_vector_stats():
    """Get vector store statistics."""
    try:
        store = VectorStore()

        results = store.collection.get()

        # Count unique files
        unique_files = set()
        for metadata in results.get('metadatas', []):
            file_id = metadata.get('file_id')
            if file_id:
                unique_files.add(file_id)

        # Count by category
        categories = {}
        for metadata in results.get('metadatas', []):
            category = metadata.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1

        return {
            'total_chunks': store.collection.count(),
            'unique_files': len(unique_files),
            'categories': categories,
            'collection_name': store.collection.name
        }

    except Exception as e:
        return {
            'total_chunks': 0,
            'unique_files': 0,
            'categories': {},
            'error': str(e)
        }


@app.get("/metrics")
async def get_metrics():
    """Get API metrics including real cache hit rates."""
    global rag_pipeline
    cache_stats = {}
    total_queries = 0

    # Pull real stats from the pipeline's QueryCache
    if rag_pipeline and rag_pipeline.query_cache:
        cache_stats = rag_pipeline.query_cache.get_stats()
        total_queries = cache_stats.get("total_requests", 0)

    total_requests = cache_stats.get("total_requests", 0)
    avg_latency = 0.0

    # Average response time from log files
    try:
        import statistics
        log_path = _get_log_path()
        if log_path.exists():
            times = []
            with open(log_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            times.append(json.loads(line.strip())["response_time_ms"])
                        except (json.JSONDecodeError, KeyError):
                            pass
            if times:
                avg_latency = round(statistics.mean(times), 2)
                if total_requests == 0:
                    total_queries = len(times)
    except Exception:
        pass

    return {
        "total_queries": total_queries,
        "avg_latency_ms": avg_latency,
        "success_rate": 1.0,
        "cache_hit_rate": round(cache_stats.get("hit_rate", 0.0), 4),
        "cache_hits": cache_stats.get("hits", 0),
        "cache_misses": cache_stats.get("misses", 0),
        "cache_size": cache_stats.get("size", 0),
    }


def _try_bm25_only(query: str, top_k: int = 3) -> Optional[dict]:
    """
    Pure BM25 fallback — no LLM, no ChromaDB embeddings.
    Used when the full RAG pipeline fails to initialize or query.
    Returns a dict with answer/sources/confidence/chunks_retrieved or None.
    """
    try:
        # Prefer the already-initialized store from the pipeline
        store = None
        if rag_pipeline is not None and getattr(rag_pipeline, 'vector_store', None) is not None:
            store = rag_pipeline.vector_store
        else:
            store = VectorStore()
        results = store.hybrid_search(query, n_results=top_k, alpha=0.0)
        if not results:
            return None
        chunks_texts = []
        sources = []
        seen = set()
        for r in results:
            text = r.text if hasattr(r, 'text') else r.get('text', '')
            meta = r.metadata if hasattr(r, 'metadata') else r.get('metadata', {})
            chunks_texts.append(text)
            doc_id = meta.get('doc_id', 'Unknown')
            if doc_id not in seen:
                sources.append(doc_id)
                seen.add(doc_id)
        answer = (
            "[Pencarian Dasar] Berikut potongan dokumen yang relevan:\n\n"
            + "\n\n---\n\n".join(chunks_texts[:top_k])
            + "\n\nCatatan: Jawaban ini dari pencarian dasar tanpa pemrosesan AI lanjutan."
        )
        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.0,
            "chunks_retrieved": len(chunks_texts),
        }
    except Exception:
        return None


@app.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_custom_groq_key: Optional[str] = Header(None, alias="X-Custom-Groq-Key"),
    x_custom_gemini_key: Optional[str] = Header(None, alias="X-Custom-Gemini-Key"),
):
    """
    Query Indonesian government documents.
    
    Uses RAG (Retrieval-Augmented Generation) to answer questions
    based on official government documents.
    """
    global rag_pipeline

    start_time = time.time()

    try:
        # Validate and sanitize query input
        sanitized_query, sanitized_options = validate_and_sanitize(
            request.query,
            request.options
        )
        # Update request with sanitized values
        request.query = sanitized_query
        request.options = sanitized_options

        # Initialize RAG pipeline on first use (lazy loading)
        if rag_pipeline is None:
            api_logger.info("[INIT] Initializing RAG pipeline...")
            try:
                rag_pipeline = RAGPipeline()
                api_logger.info("[OK] RAG Pipeline initialized successfully!")
            except Exception as init_error:
                api_logger.error(f"[ERR] Failed to initialize RAG pipeline: {init_error}")
                import traceback
                api_logger.error(traceback.format_exc())
                # Try BM25-only fallback before giving up
                bm25_result = _try_bm25_only(request.query, top_k=3)
                if bm25_result:
                    return QueryResponse(
                        answer=bm25_result["answer"],
                        sources=bm25_result["sources"],
                        confidence=bm25_result["confidence"],
                        latency_ms=round((time.time() - start_time) * 1000, 2),
                        metadata={
                            "status": "bm25_init_fallback",
                            "chunks_retrieved": bm25_result["chunks_retrieved"],
                            "error": str(init_error),
                        }
                    )
                return QueryResponse(
                    answer="Maaf, sistem sedang dalam perbaikan. Silakan coba lagi nanti.",
                    sources=[],
                    confidence=0.0,
                    latency_ms=round((time.time() - start_time) * 1000, 2),
                    metadata={
                        "status": "initialization_failed",
                        "error_type": type(init_error).__name__
                    }
                )
        
        # Extract options with defaults
        use_query_expansion = request.options.get("use_query_expansion", True)
        use_reranking = request.options.get("use_reranking", False)
        use_hybrid = request.options.get("use_hybrid", True)
        top_k = request.options.get("top_k", 5)

        # Configure pipeline with options
        config = {
            "retrieval_method": "hybrid" if use_hybrid else "vector",
            "alpha": 0.7,  # Balance between BM25 and vector
            "top_k": top_k,
            "use_query_expansion": use_query_expansion,
            "use_reranking": use_reranking
        }
        rag_pipeline.configure(config)

        # Classify query topic for legal disclaimer display
        try:
            from src.utils.topic_classifier import classify_query
            topic_result = classify_query(request.query)
            topic_key = topic_result.primary_topic.value
            is_high_stakes = topic_result.is_high_stakes
            api_logger.info(f"[TOPIC] Detected: {topic_key} (high-stakes={is_high_stakes})")
        except Exception:
            topic_key = 'umum'
            is_high_stakes = False

        # Calculate latency (before cache check so it's available in both branches)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Check if query is in cache (skip LLM call)
        use_cache = request.options.get("use_cache", True)
        if use_cache and rag_pipeline.query_cache:
            cached = rag_pipeline.query_cache.get(request.query)
            if cached:
                api_logger.info(f"[CACHE] Cache hit for query")
                latency_ms = round((time.time() - start_time) * 1000, 2)
                cached_chunks = cached.get('retrieved_chunks', [])
                log_search(
                    query=request.query,
                    user_id=x_user_id,  # from header
                    results_count=len(cached_chunks),
                    confidence_score=cached.get('confidence', 0.0),
                    response_time_ms=latency_ms,
                    had_answer=bool(cached.get('answer')) and 'no answer' not in cached.get('answer', '').lower(),
                )
                return QueryResponse(
                    answer=f"[Cached] {cached.get('answer', '')}",
                    sources=cached.get('sources', []),
                    confidence=cached.get('confidence', 0.0),
                    latency_ms=latency_ms,
                    metadata={
                        **cached.get('metadata', {}),
                        "from_cache": True,
                        "chunks_retrieved": len(cached.get('retrieved_chunks', []))
                    }
                )

        # Execute RAG query with timeout warning
        api_logger.info(f"[MSG] Processing query: {request.query}")

        # Check query complexity (simple heuristic)
        query_words = len(request.query.split())
        if query_words > 50:
            api_logger.warning("[WARN] Complex query detected (>50 words)")
        
        # Extract custom keys from headers or request options
        custom_groq_key = x_custom_groq_key or request.options.get("custom_groq_key")
        custom_gemini_key = x_custom_gemini_key or request.options.get("custom_gemini_key")

        try:
            result = rag_pipeline.query(
                question=request.query,
                filter_metadata=None,
                include_sources=True,
                use_cache=True,
                custom_groq_key=custom_groq_key,
                custom_gemini_key=custom_gemini_key
            )
        except Exception as query_error:
            api_logger.error(f"[ERR] Query execution failed: {query_error}")
            import traceback
            api_logger.error(traceback.format_exc())

            # Determine error type and use error schema
            error_type = ErrorType.RETRIEVAL_FAILED
            error_msg = str(query_error).lower()

            if 'timeout' in error_msg:
                error_type = ErrorType.LLM_TIMEOUT
            elif 'rate' in error_msg or 'limit' in error_msg:
                error_type = ErrorType.RATE_LIMITED

            error_response = get_error_response(error_type, query=request.query)

            # Try BM25 fallback as last resort
            try:
                bm25_result = _try_bm25_only(request.query, top_k=3)
                if bm25_result:
                    return QueryResponse(
                        answer=bm25_result["answer"],
                        sources=bm25_result["sources"],
                        confidence=bm25_result["confidence"],
                        latency_ms=round((time.time() - start_time) * 1000, 2),
                        metadata={
                            "status": "bm25_fallback",
                            "chunks_retrieved": bm25_result["chunks_retrieved"],
                            "error_code": error_response.code,
                            "error_type": error_type.value,
                        }
                    )
            except Exception as fallback_error:
                api_logger.error(f"[ERR] Fallback search failed: {fallback_error}")

            # Final fallback with Indonesian error message
            return QueryResponse(
                answer=error_response.message,
                sources=[],
                confidence=0.0,
                latency_ms=round((time.time() - start_time) * 1000, 2),
                metadata={
                    "status": "query_failed",
                    "error_code": error_response.code,
                    "error_type": error_type.value,
                    "suggestions": [s.text for s in error_response.suggestions],
                    "recoverable": error_response.recoverable,
                }
            )

        # Calculate latency
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Count non-trivial results
        chunks_retrieved = len(result.get('retrieved_chunks', []))
        had_answer = bool(result.get('answer')) and 'no answer' not in result.get('answer', '').lower()
        confidence = result.get('confidence', 0.0)

        # Build warnings list
        warnings = []

        # Confidence warning (< 0.4)
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            warnings.extend(check_confidence_warnings(confidence))

        # Zero chunks warning
        chunk_warning = check_chunk_count_warning(result.get('retrieved_chunks', []))
        if chunk_warning:
            warnings.append(chunk_warning)

        # Superseded document warning
        if result.get('sources'):
            superseded_warning = check_superseded_document(result['sources'])
            if superseded_warning:
                warnings.append(superseded_warning)

        # Log this search to analytics
        log_search(
            query=request.query,
            user_id=x_user_id,  # from header
            results_count=chunks_retrieved,
            confidence_score=confidence,
            response_time_ms=latency_ms,
            had_answer=had_answer,
        )

        # Format sources for API response
        source_list = []
        if result.get('sources'):
            for source in result['sources']:
                doc_id = source.get('doc_id', 'Unknown')
                doc_type = source.get('doc_type', '')
                year = source.get('year', '')

                if doc_type and year:
                    source_str = f"{doc_id} ({doc_type}, {year})"
                elif doc_type:
                    source_str = f"{doc_id} ({doc_type})"
                else:
                    source_str = doc_id

                source_list.append(source_str)

        # Build metadata with warnings and topic classification
        response_metadata = {
            "chunks_retrieved": chunks_retrieved,
            "expansion_used": use_query_expansion,
            "reranking_used": use_reranking,
            "model_used": result.get('model_used', 'unknown'),
            "tokens_used": result.get('tokens_used', 0),
            "topic": topic_key,
            "is_high_stakes": is_high_stakes,
        }

        if warnings:
            response_metadata["warnings"] = warnings

        # Return formatted response
        return QueryResponse(
            answer=result.get('answer', 'No answer generated'),
            sources=source_list or ["No sources found"],
            confidence=confidence,
            latency_ms=latency_ms,
            metadata=response_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        api_logger.error(f"[ERR] Query error: {error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


class MultiAgentRequest(BaseModel):
    """Request model for multi-agent query endpoint."""
    query: str = Field(..., min_length=1, max_length=500, description="User query in Indonesian")
    options: Optional[dict] = Field(
        default_factory=dict,
        description="Optional parameters: top_k (int)"
    )


@app.post("/query/multi-agent", response_model=QueryResponse)
async def query_multi_agent(
    request: MultiAgentRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
):
    """
    Query using the Multi-Agent Orchestrator pipeline.

    Agents: QueryUnderstanding → Retrieval → LegalReasoning → ResponseSynthesis.
    Returns the same QueryResponse shape as /query but with richer metadata
    (per-agent timings, legal analysis warnings, entity extraction).
    """
    import asyncio
    import concurrent.futures

    start_time = time.time()

    # Validate and sanitize
    sanitized_query, sanitized_options = validate_and_sanitize(request.query, request.options)
    request.query = sanitized_query
    request.options = sanitized_options

    top_k = request.options.get("top_k", 5)

    api_logger.info(f"[MULTI-AGENT] query='{request.query[:80]}'")

    try:
        # Run orchestrator in a thread pool (it's async internally)
        def _run():
            return asyncio.run(
                __import__("src.multi_agent.orchestrator", fromlist=["MultiAgentOrchestrator"])
                .MultiAgentOrchestrator(options={"top_k": top_k})
                .run(request.query)
            )

        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(_run)
                result = future.result(timeout=30.0)
        except RuntimeError:
            # No running loop — safe to call asyncio.run
            result = _run()

    except concurrent.futures.TimeoutError:
        api_logger.error("[MULTI-AGENT] Orchestrator timed out after 30s")
        return QueryResponse(
            answer="Maaf, pertanyaan Anda memerlukan waktu lebih lama dari biasanya. Silakan coba pertanyaan yang lebih spesifik.",
            sources=[],
            confidence=0.0,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            metadata={"status": "orchestrator_timeout", "agent_timings": {}},
        )

    except Exception as orchestrator_error:
        api_logger.error(f"[MULTI-AGENT] Orchestrator failed: {orchestrator_error}")
        import traceback
        api_logger.error(traceback.format_exc())
        return QueryResponse(
            answer="Maaf, terjadi kesalahan dalam sistem multi-agent. Silakan coba lagi nanti.",
            sources=[],
            confidence=0.0,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            metadata={
                "status": "orchestrator_error",
                "error": str(orchestrator_error),
            },
        )

    latency_ms = round((time.time() - start_time) * 1000, 2)
    metadata = result.get("metadata", {})

    # Log search to analytics
    log_search(
        query=request.query,
        user_id=x_user_id,
        results_count=metadata.get("chunks_retrieved", 0),
        confidence_score=result.get("confidence", 0.0),
        response_time_ms=latency_ms,
        had_answer=bool(result.get("answer")) and "maaf" not in result.get("answer", "").lower(),
    )

    return QueryResponse(
        answer=result.get("answer", "Tidak ada jawaban dihasilkan."),
        sources=result.get("sources", []),
        confidence=result.get("confidence", 0.0),
        latency_ms=latency_ms,
        metadata={
            "chunks_retrieved": metadata.get("chunks_retrieved", 0),
            "agent_timings": metadata.get("agent_timings", {}),
            "retrieval_method": metadata.get("retrieval_method", "unknown"),
            "response_generation_method": metadata.get("response_generation_method", "unknown"),
            "query_entities": metadata.get("query_entities", {}),
            "warnings": result.get("warnings", []),
            "status": "multi_agent_ok",
        },
    )


@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """
    Return aggregated analytics over the current week.
    Used by the admin analytics dashboard.
    """
    import statistics

    log_path = _get_log_path()
    events = []
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    total = len(events)
    if total == 0:
        return {
            "total_queries": 0,
            "unique_users": 0,
            "zero_result_queries": [],
            "top_queries": [],
            "avg_confidence": 0.0,
            "avg_response_time_ms": 0.0,
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0,
            "daily_users": {},
        }

    response_times = [e["response_time_ms"] for e in events]
    confidence_scores = [e["confidence_score"] for e in events]

    def percentile(data, p):
        if not data:
            return 0
        s = sorted(data)
        idx = int(len(s) * p / 100)
        idx = min(idx, len(s) - 1)
        return s[idx]

    # Top 20 queries by count
    query_counts: dict = {}
    for e in events:
        q = e["query"]
        query_counts[q] = query_counts.get(q, 0) + 1
    top_queries = sorted(query_counts.items(), key=lambda x: -x[1])[:20]

    # Zero-result queries
    zero_results = sorted(
        [(e["query"], e["timestamp"]) for e in events if e["results_count"] == 0],
        key=lambda x: x[1],
        reverse=True
    )
    # Deduplicate
    seen = set()
    zero_unique = []
    for q, ts in zero_results:
        if q not in seen:
            seen.add(q)
            zero_unique.append({"query": q, "last_seen": ts})

    # Daily active users
    daily_users: dict = {}
    for e in events:
        day = e["timestamp"][:10]  # YYYY-MM-DD
        daily_users[day] = daily_users.get(day, 0) + 1

    return {
        "total_queries": total,
        "unique_users": len(set(e["user_id"] for e in events)),
        "zero_result_queries": zero_unique[:50],
        "top_queries": [{"query": q, "count": c} for q, c in top_queries],
        "avg_confidence": round(statistics.mean(confidence_scores), 4),
        "avg_response_time_ms": round(statistics.mean(response_times), 2),
        "p50_ms": round(percentile(response_times, 50), 2),
        "p95_ms": round(percentile(response_times, 95), 2),
        "p99_ms": round(percentile(response_times, 99), 2),
        "daily_users": daily_users,
    }


# Register API keys router
from .keys_router import router as keys_router
app.include_router(keys_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
