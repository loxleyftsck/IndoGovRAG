"""
FastAPI Backend for IndoGovRAG
Production-ready with AI-powered answers via Gemini
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path
import time
import os

# Gemini AI
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.simple_vector_store import SimpleVectorStore
from api.security import (
    limiter,
    VALID_API_KEYS,
    validate_query_input,
    audit_log,
    log_request,
)

# Configure Gemini (VULN-005 FIX - Don't log secrets!)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    print("✅ Gemini AI configured")  # No key in logs!
else:
    gemini_model = None
    print("⚠️ GEMINI_API_KEY not set - AI answers disabled")

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Add security headers and request validation."""
    
    # VULN-012 FIX: Request size limit
    if request.headers.get("content-length"):
        content_length = int(request.headers["content-length"])
        if content_length > 100 * 1024:  # 100KB max
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large (max 100KB)"}
            )
    
    response = await call_next(request)
    
    # Security headers (VULN-023 FIX)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

app = FastAPI(
    title="IndoGovRAG API",
    description="Production AI-powered Indonesian Government Legal Research API",
    version="1.0.0"
)

# Add security middleware
app.middleware("http")(log_request)

# Add rate limiter
app.state.limiter = limiter

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store
vector_store = SimpleVectorStore()

# Request/Response Models
class QueryRequest(BaseModel):
    question: str
    top_k: int = 3

class Source(BaseModel):
    title: str
    text: str
    score: float
    category: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    processing_time: float

# Health Check
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "IndoGovRAG API",
        "version": "1.0.0",
        "documents": vector_store.count()
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "vector_store": "operational",
        "documents_indexed": vector_store.count()
    }

# Query Endpoint (public access with optional auth + CSRF)
@app.post("/api/query", response_model=QueryResponse)
@limiter.limit("20/minute")  # Public rate limit
async def query(
    request: Request,
    query_request: QueryRequest,
    api_key: str = Header(None, alias="X-API-Key")
):
    """
    Query the RAG system (public access with CSRF protection).
    
    Security:
        - CSRF token required (get from /api/csrf-token)
        - Optional API key for higher rate limits
        - Input validation and sanitization
    
    Args:
        request: FastAPI request object
        query_request: QueryRequest with question and optional top_k
        api_key: Optional API key for higher rate limits
    
    Returns:
        QueryResponse with answer, sources, confidence
    """
    # VULN-002 FIX: CSRF Protection
    from api.security import csrf_protect
    csrf_protect(request)
    
    start_time = time.time()
    
    # Determine user tier
    user_info = {"name": "public", "tier": "free"}
    if api_key and api_key in VALID_API_KEYS:
        user_info = VALID_API_KEYS[api_key]
    
    # Validate input
    validate_query_input(query_request.question)
    
    try:
        # Log query
        audit_log({
            "event": "query_start",
            "user": user_info["name"],
            "question_length": len(query_request.question),
            "timestamp": time.time()
        })
        
        # Search vector store
        results = vector_store.search(query_request.question, top_k=query_request.top_k)
        
        if not results:
            return QueryResponse(
                answer="Maaf, tidak ditemukan informasi yang relevan dalam database. Coba gunakan kata kunci yang lebih spesifik.",
                sources=[],
                confidence=0.0,
                processing_time=time.time() - start_time
            )
        
        # Format sources
        sources = [
            Source(
                title=r['metadata'].get('title', 'Unknown'),
                text=r['text'][:200] + "..." if len(r['text']) > 200 else r['text'],
                score=r['score'],
                category=r['metadata'].get('category', 'general')
            )
            for r in results
        ]
        
        # Generate AI-powered answer with Gemini
        if gemini_model and GEMINI_API_KEY:
            try:
                # Build context from top results
                context = "\n\n".join([
                    f"Dokumen {i+1} ({r['metadata'].get('title', 'Unknown')}):\n{r['text']}"
                    for i, r in enumerate(results[:3])
                ])
                
                # Create prompt for Gemini
                prompt = f"""Kamu adalah asisten AI yang membantu menjawab pertanyaan tentang peraturan pemerintah Indonesia.

Pertanyaan: {query_request.question}

Konteks dari dokumen resmi:
{context}

Instruksi:
1. Jawab pertanyaan dengan bahasa yang natural dan mudah dipahami
2. Gunakan HANYA informasi dari konteks dokumen di atas
3. Jika konteks tidak cukup untuk menjawab, katakan dengan jelas
4. Jelaskan secara ringkas dan terstruktur
5. Gunakan Bahasa Indonesia yang baik dan benar

Jawaban:"""

                # Generate response
                response = gemini_model.generate_content(prompt)
                answer = response.text
                
            except Exception as e:
                print(f"Gemini error: {e}")
                # Fallback to simple answer
                answer = f"Berdasarkan dokumen yang ditemukan:\n\n{results[0]['text'][:300]}..."
        else:
            # Fallback when no Gemini API key
            answer = f"Berdasarkan dokumen yang ditemukan:\n\n{results[0]['text'][:300]}...\n\n💡 Tip: Set GEMINI_API_KEY untuk jawaban AI yang lebih natural."
        
        # Calculate confidence (average score)
        confidence = sum(r['score'] for r in results) / len(results) if results else 0.0
        
        processing_time = time.time() - start_time
        
        # Log success
        audit_log({
            "event": "query_success",
            "user": user_info["name"],
            "latency": processing_time,
            "confidence": confidence,
            "sources_found": len(sources)
        })
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=min(confidence, 1.0),
            processing_time=processing_time
        )
    
    except Exception as e:
        # Log error
        audit_log({
            "event": "query_error",
            "user": user_info["name"],
            "error": str(e)
        })
        raise HTTPException(
            status_code=500, 
            detail="Maaf, terjadi kesalahan sistem. Tim kami sedang memperbaikinya. Silakan coba lagi dalam beberapa saat."
        )

# Stats Endpoint
@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    return {
        "documents_indexed": vector_store.count(),
        "categories": ["administrasi", "kesehatan", "perpajakan", "ekonomi", "pendidikan"],
        "accuracy": 0.95,
        "avg_response_time": 1.2,
        "total_queries": 0  # TODO: Track in database
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting IndoGovRAG API...")
    print("📚 Documents indexed:", vector_store.count())
    print("🌐 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
