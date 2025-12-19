"""
FastAPI Application for IndoGovRAG

Production-ready API endpoints for RAG query system.
"""

import os
import time
from typing import Optional
from contextlib import asynccontextmanager

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
            # TODO: Import and initialize actual RAG pipeline
            # from src.rag.pipeline import RAGPipeline
            # rag_pipeline = RAGPipeline()
            
            # For now, return mock response
            return QueryResponse(
                answer="RAG pipeline not yet initialized. This is a placeholder response.",
                sources=["System"],
                confidence=0.0,
                latency_ms=round((time.time() - start_time) * 1000, 2),
                metadata={
                    "status": "pipeline_not_initialized",
                    "query": request.query
                }
            )
        
        # Execute query
        # result = rag_pipeline.query(
        #     query=request.query,
        #     **request.options
        # )
        
        # Calculate latency
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # Return mock response for now
        return QueryResponse(
            answer=f"Mock answer for: {request.query}",
            sources=["Document A", "Document B"],
            confidence=0.85,
            latency_ms=latency_ms,
            metadata={
                "chunks_retrieved": request.options.get("top_k", 5),
                "expansion_used": request.options.get("use_query_expansion", False),
                "reranking_used": request.options.get("use_reranking", False)
            }
        )
        
    except Exception as e:
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
