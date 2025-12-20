"""
FastAPI Application for IndoGovRAG

Production-ready API endpoints for RAG query system.
"""

import os
import sys
import time
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to Python path to allow imports from src/
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RAG pipeline (will create on first use)
rag_pipeline = None


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., min_length=1, max_length=500, description="User query in Indonesian")
    options: Optional[dict] = Field(default_factory=dict, description="Optional search parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Apa syarat membuat KTP elektronik?",
                "options": {
                    "use_query_expansion": True,
                    "use_reranking": True,
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
    print("🚀 Starting IndoGovRAG API...")
    
    # Initialize RAG pipeline (lazy loading)
    # Actual initialization happens on first query to save memory
    
    yield
    
    # Shutdown
    print("🛑 Shutting down IndoGovRAG API...")


# Create FastAPI app
app = FastAPI(
    title="IndoGovRAG API",
    description="AI-Powered Search Engine for Indonesian Government Documents",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global rag_pipeline
    
    return {
        "status": "healthy",
        "rag_initialized": rag_pipeline is not None,
        "gemini_api_key_set": bool(os.getenv("GEMINI_API_KEY")),
        "timestamp": time.time()
    }


@app.get("/metrics")
async def get_metrics():
    """Get API metrics."""
    # TODO: Implement metrics collection
    return {
        "total_queries": 0,
        "avg_latency_ms": 0,
        "success_rate": 1.0,
        "cache_hit_rate": 0.0
    }


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query Indonesian government documents.
    
    Uses RAG (Retrieval-Augmented Generation) to answer questions
    based on official government documents.
    """
    global rag_pipeline
    
    start_time = time.time()
    
    try:
        # Initialize RAG pipeline on first use (lazy loading)
        if rag_pipeline is None:
            print("🔧 Initializing RAG pipeline...")
            try:
                from src.rag.pipeline import RAGPipeline
                rag_pipeline = RAGPipeline()
                print("✅ RAG Pipeline initialized successfully!")
            except Exception as init_error:
                print(f"❌ Failed to initialize RAG pipeline: {init_error}")
                import traceback
                traceback.print_exc()
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
        
        # Extract options
        use_query_expansion = request.options.get("use_query_expansion", False)
        use_reranking = request.options.get("use_reranking", False)
        top_k = request.options.get("top_k", 5)
        
        # Execute RAG query with timeout warning
        print(f"📝 Processing query: {request.query}")
        
        # Check query complexity (simple heuristic)
        query_words = len(request.query.split())
        if query_words > 50:
            print("⚠️ Complex query detected (>50 words)")
        
        try:
            result = rag_pipeline.query(
                question=request.query,
                filter_metadata=None,
                include_sources=True
            )
        except Exception as query_error:
            print(f"❌ Query execution failed: {query_error}")
            import traceback
            traceback.print_exc()
            return QueryResponse(
                answer="Maaf, query Anda tidak dapat diproses. Silakan coba dengan pertanyaan yang lebih sederhana.",
                sources=[],
                confidence=0.0,
                latency_ms=round((time.time() - start_time) * 1000, 2),
                metadata={
                    "status": "query_failed",
                    "error_type": type(query_error).__name__
                }
            )
        
        # Calculate latency
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
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
        
        # Return formatted response
        return QueryResponse(
            answer=result.get('answer', 'No answer generated'),
            sources=source_list or ["No sources found"],
            confidence=result.get('confidence', 0.0),
            latency_ms=latency_ms,
            metadata={
                "chunks_retrieved": len(result.get('retrieved_chunks', [])),
                "expansion_used": use_query_expansion,
                "reranking_used": use_reranking,
                "model_used": result.get('model_used', 'unknown'),
                "tokens_used": result.get('tokens_used', 0)
            }
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Query error: {error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


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
