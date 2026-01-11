"""
FastAPI main application with full observability instrumentation
"""

import os
import sys
import time
import uuid
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# === OBSERVABILITY IMPORTS ===
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.monitoring.tracing import setup_tracing, tracer
from src.monitoring.metrics import (
    track_query_success,
    track_query_error,
    observe_latency,
    observe_retrieval_latency,
    observe_llm_latency,
    observe_cost,
    observe_confidence
)

# Load environment
load_dotenv()

# Initialize tracing
setup_tracing(
    service_name="indogovrag",
    environment=os.getenv("ENVIRONMENT", "production")
)

# RAG pipeline (lazy load)
rag_pipeline = None


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    options: Optional[dict] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    sources: list
    confidence: float
    latency_ms: float
    metadata: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager"""
    print("🚀 Starting IndoGovRAG API...")
    yield
    print("🛑 Shutting down...")


# Create app
app = FastAPI(
    title="IndoGovRAG API",
    description="AI-Powered Search for Indonesian Government Documents",
    version="1.0.0",
    lifespan=lifespan
)

# === OBSERVABILITY INSTRUMENTATION ===

# Auto-instrument FastAPI (creates spans for all endpoints)
FastAPIInstrumentor.instrument_app(app)

# Request ID middleware
@app.middleware("http")
async def add_request_id_and_trace(request: Request, call_next):
    """
    Add unique request ID to all requests
    Links to trace for debugging
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add to active span
    span = trace.get_current_span()
    if span:
        span.set_attribute("request.id", request_id)
        span.set_attribute("request.method", request.method)
        span.set_attribute("request.path", request.url.path)
        span.set_attribute("request.client_ip", request.client.host)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === ENDPOINTS ===

@app.get("/")
async def root():
    return {
        "message": "IndoGovRAG API",
        "version": "1.0.0",
        "observability": {
            "tracing": "enabled",
            "metrics": "/metrics",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "rag_initialized": rag_pipeline is not None,
        "api_key_set": bool(os.getenv("GEMINI_API_KEY"))
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest, http_request: Request):
    """
    Query RAG system with full observability
    """
    global rag_pipeline
    
    start_time = time.time()
    request_id = http_request.state.request_id
    
    # Start manual span for detailed tracking
    with tracer.start_as_current_span("rag_query_processing") as span:
        # Set span attributes
        span.set_attribute("query.text", request.query[:100])
        span.set_attribute("query.length", len(request.query))
        span.set_attribute("request.id", request_id)
        
        try:
            # Initialize pipeline if needed
            if rag_pipeline is None:
                with tracer.start_as_current_span("pipeline_initialization"):
                    from src.rag.pipeline import RAGPipeline
                    rag_pipeline = RAGPipeline()
            
            # Execute query with tracing
            result = rag_pipeline.query(request.query)
            
            # Calculate metrics
            latency = time.time() - start_time
            cost = (result.get('tokens_used', 0) / 1000) * 0.00015
            
            # Set span attributes
            span.set_attribute("answer.length", len(result['answer']))
            span.set_attribute("confidence", result['confidence'])
            span.set_attribute("model", result['model_used'])
            span.set_attribute("tokens", result['tokens_used'])
            span.set_attribute("cost_usd", cost)
            span.set_attribute("latency_seconds", latency)
            
            # Track metrics
            track_query_success(model=result['model_used'])
            observe_latency(latency)
            observe_cost(cost)
            observe_confidence(result['confidence'])
            
            # Format sources
            source_list = [
                f"{s['doc_id']} ({s.get('doc_type', '')}, {s.get('year', '')})"
                for s in result.get('sources', [])
            ]
            
            return QueryResponse(
                answer=result['answer'],
                sources=source_list,
                confidence=result['confidence'],
                latency_ms=round(latency * 1000, 2),
                metadata={
                    "request_id": request_id,
                    "chunks_retrieved": len(result.get('retrieved_chunks', [])),
                    "model_used": result['model_used'],
                    "tokens_used": result['tokens_used'],
                    "cost_usd": round(cost, 6)
                }
            )
            
        except Exception as e:
            # Track error
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            
            track_query_error(error_type=type(e).__name__)
            
            raise HTTPException(
                status_code=500,
                detail=f"Query failed: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    from fastapi.responses import Response
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
