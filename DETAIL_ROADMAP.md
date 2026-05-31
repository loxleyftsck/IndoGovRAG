# 🗺️ INDOgravRAG - DETAIL ROADMAP
**Last Updated:** 2024-12-19
**Version:** v1.0-alpha → v2.0
**Security:** A- (90/100) ✅
**Documents:** 18 (manual) + ~40 (scraping)

---

## 📊 CURRENT STATE ANALYSIS

### What EXISTS Now:

**Backend (FastAPI + Python):**
```
src/
├── data/           → loader, chunker, preprocessor, PII detector
├── embeddings/     → custom embeddings, cache, benchmark
├── evaluation/     → RAGAS evaluator, A/B testing, experiment tracker
├── llm/            → Groq LLM, multi-tier fallback (5 tiers!)
├── monitoring/     → Gemini quota tracker, wrapper
├── rag/            → pipeline (the core!), prompts
├── retrieval/      → BM25, vector search, reranker, query expander, cache
├── utils/          → topic classifier
└── errors/         → error schemas
```
✅ 33 Python modules across 8 subsystems
✅ Groq multi-tier with 5 fallbacks
✅ BM25 + vector hybrid search
✅ Query expansion + reranking
✅ RAGAS evaluation framework

**Frontend (Next.js 16 + React 19):**
```
frontend/app/
├── page.tsx              → Main search (AI answers)
├── layout.tsx           → DM Serif Display + DM Sans fonts
├── providers.tsx         → TanStack Query + QueryClient
├── globals.css          → Full design system (CSS vars, animations)
├── search/
│   ├── page.tsx         → Search results (URL-param driven)
│   └── components/
│       ├── SearchFilters.tsx    → Left sidebar (jenis, status, tahun, etc.)
│       ├── ActiveFilters.tsx    → Right sidebar (chips, suggestions)
│       ├── SearchResultCard.tsx → Individual result card
│       ├── SearchSummary.tsx    → Top bar (query, count, time)
│       ├── ConfidenceGauge.tsx  → Recharts gauge
│       ├── SkeletonLoader.tsx  → Framer Motion skeletons
│       └── Pagination.tsx        → Page controls
├── components/
│   ├── DocumentManager.tsx      → Upload UI (port 8000 fixed)
│   ├── EnhancedSearchResults.tsx
│   ├── ConfidenceBadge.tsx
│   ├── LegalDisclaimer.tsx
│   └── SourceCard.tsx
├── upload/page.tsx
└── admin/analytics/page.tsx
```
✅ 8 search components + TanStack Query
✅ Zustand store (searchStore.ts)
✅ Framer Motion animations
✅ DM Serif Display / DM Sans typography
✅ Full CSS design system

**Infrastructure:**
```
✅ ChromaDB vector store (data/vector_db/)
✅ Groq API (llama-3.3-70b, mixtral, gemma2)
✅ FastAPI with CORS, rate limiting, security headers
✅ Docker + docker-compose.yml
✅ Makefile (install, dev, test, docker-*)
✅ GitHub Actions CI
✅ Fly.io deployment config
```

### What is BROKEN / INCOMPLETE:

1. **RAG pipeline** → UnicodeEncodeError saat init → ChromaDB path/env encoding issue
2. **Search page** → `/search` route exists but not fully functional (API mismatch)
3. **No integration** between `/` (AI answer) and `/search` (list results) routes
4. **Groq API key** → exposed in `.env` (should be via backend env, not frontend)
5. **No auth** → all users share same state
6. **Vector DB** → only 3 chunks, not 18 docs indexed
7. **Scraper** → status unknown, may have stalled

---

## 🎯 ROADMAP PHASES

### PHASE 1: FIX & STABILIZE (1-2 days)
*"Make what we have actually work"*

#### 1.1 Fix RAG Pipeline Unicode Error
**Problem:** `UnicodeEncodeError` on `safe_print()` when ChromaDB initializes
**Root cause:** `sys.stdout.encoding` is `cp1252` on Windows, fails on Indonesian chars
**Fix:**
```python
# src/rag/pipeline.py - change safe_print:
import io
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Force UTF-8 output on Windows
        import sys
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            print(*args, **kwargs)
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

Or better: replace all `safe_print` with Python `logging` module throughout:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Initialized RAG with {len(chunks)} chunks")
```
→ Remove `safe_print` entirely, use proper logging

#### 1.2 Fix ChromaDB Initialization Path
**Problem:** ChromaDB uses Windows path `data\vector_db\chroma` which may cause issues
**Fix:** Ensure ChromaDB `persist_directory` uses forward slashes or Pathlib:
```python
from pathlib import Path
persist_dir = str(Path("data/vector_db/chroma").resolve())
client = chromadb.PersistentClient(path=persist_dir)
```

#### 1.3 Index All 18 Documents
**Problem:** Only 3 chunks in ChromaDB
**Fix:** Run document ingestion script:
```bash
python scripts/index_documents.py
# or
python -c "from src.data.loader import DocumentLoader; ..."
```
Create `scripts/reindex_all.py` that:
1. Loads all 18 documents from `data/documents/`
2. Chunks them (512 tokens, 64 overlap)
3. Embeds with `intfloat/multilingual-e5-base`
4. Stores in ChromaDB
5. Reports stats: X docs, Y chunks, Z unique types

#### 1.4 Verify All Endpoints
**Current endpoints (from OpenAPI):**
```
GET  /                    → OK
GET  /health              → OK
POST /query               → needs "query" not "prompt"
GET  /files               → OK (returns {"files": [], ...})
GET  /stats               → OK (returns {"total_chunks": 5, ...})
POST /upload/file         → OK
POST /upload/folder       → OK
GET  /upload/status/{id}  → OK
DELETE /upload/delete/{id} → OK
GET  /files/clear         → OK
DELETE /files/clear       → OK
GET  /metrics             → OK
GET  /api/analytics/summary → OK
```

**Problem:** No dedicated search/filter endpoint for `/search` page.
- Current: `POST /query` with `{query: str, options: {...}}`
- Expected by search page: paginated list of documents with filters

**Solution:** Either:
1. Add new `GET /search` endpoint with query params
2. Adapt search page to call `POST /query` and transform answer into doc list

#### 1.5 Test Full Flow
```
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"syarat pembuatan KTP"}'

# Should return: answer + sources + confidence + latency_ms
```
If this works → Phase 1 done ✅

---

### PHASE 2: SEARCH PAGE INTEGRATION (2-3 days)
*"Connect /search page to actual backend"*

#### 2.1 Define Search API Contract
The `/search` page needs:
```typescript
// Request: GET /search?q=...&jenis=UU,PP&status=berlaku&...
// Response:
{
  "documents": [
    {
      "id": "doc_001",
      "title": "Undang-Undang Nomor 24 Tahun 2013",
      "jenis": "UU",
      "tahun": 2013,
      "nomor": "24",
      "instansi": "Kementerian Dalam Negeri",
      "status": "berlaku",
      "excerpt": "Undang-undang tentang perubahan atas UU 23/2006...",
      "citations": 847,
      "relevance_score": 0.94
    },
    ...
  ],
  "total": 142,
  "page": 1,
  "per_page": 10,
  "facets": {
    "jenis": {"UU": 89, "PP": 31, "Perpres": 22},
    "status": {"berlaku": 130, "direvisi": 10, "dicabut": 2},
    "tahun_range": {"min": 1945, "max": 2025}
  }
}
```

Since `/query` returns a text answer (not document list), we have two options:

**Option A:** Build new `GET /documents/search` endpoint (cleaner, dedicated)
**Option B:** Have search page call `/query` and parse answer to extract doc references

→ **Recommendation: Option A** (proper REST design, enables faceted search)

#### 2.2 Build `/documents/search` Endpoint
```python
# api/search.py (new file)
@router.get("/documents/search")
async def search_documents(
    q: str = Query(..., min_length=1),
    jenis: str = Query(""),        # comma-separated: UU,PP
    status: str = Query("berlaku"),
    tahun_dari: int = Query(None),
    tahun_sampai: int = Query(None),
    instansi: str = Query(""),
    sort: str = Query("relevansi"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    api_key: str = Header(None, alias="X-API-Key"),
):
    # 1. Validate & sanitize query
    # 2. Get all docs from vector store matching criteria
    # 3. Apply filters (jenis, status, tahun, instansi)
    # 4. Sort (relevansi = vector score, terbaru = tahun desc, etc.)
    # 5. Paginate
    # 6. Return {documents, total, page, per_page, facets}
```

#### 2.3 Connect Search Page to API
Update `frontend/app/search/page.tsx`:
```typescript
// TanStack Query fetch
const { data } = useQuery({
  queryKey: ['search', searchParams],
  queryFn: () => fetch(`/documents/search?${params}`).then(r => r.json()),
  staleTime: 30_000,
})
```

#### 2.4 Wire Up Zustand ↔ URL Sync
The search page should:
1. Read URL params on mount → hydrate Zustand store
2. On filter change → update Zustand + router.push(new URL)
3. On page load → read searchParams → trigger API call

#### 2.5 Add Document Cards
- Render `SearchResultCard` for each document
- Show: jenis badge, title, excerpt, tahun, instansi, status, citations
- Add: hover effects, relevance score bar, click to full doc

#### 2.6 Connect to `/query` (for AI answers)
The search results page should ALSO call `/query` for AI-generated answer summary at the top.
```
Top of search page:
┌─────────────────────────────────────────────┐
│ 🤖 AI Answer (from /query)                  │
│ "Berdasarkan UU 24/2013, syarat KTP adalah.."│
│ [Confidence: 92%] [Sources: 4 docs]          │
└─────────────────────────────────────────────┘

Below:
┌─────────────────────────────────────────────┐
│ 📄 Search Results (from /documents/search)   │
│ Showing 10 of 142 documents                  │
│ [Document 1] [Document 2] ... [Document 10]  │
└─────────────────────────────────────────────┘
```

---

### PHASE 3: CONTENT PIPELINE (3-5 days)
*"Get 50+ real documents indexed"*

#### 3.1 Document Ingestion Pipeline
```bash
scripts/
├── index_documents.py        # Run this to index all docs
├── reindex_all.py            # Clear + reindex everything
├── validate_index.py         # Verify ChromaDB has all docs
├── check_dataset.py          # Validate document quality
└── validate_dataset.py       # Check for corrupt/empty docs
```

#### 3.2 Document Categories to Build
**Current (18 docs):** Identitas (5), Keluarga (3), Transportasi (3), Pajak (2), Properti (1), Ketenagakerjaan (3), Bisnis (1)

**Target (50+ docs):** Add these categories:
- **Keuangan (5):** POJK tentang公平, OJK tentang bank, UU Perbankan, UU OJK, SKBDN
- **Pertanahan (3):** Sertifikat Tanah, PBB, Girik/C1
- **Imigrasi (3):** Visa, KITAS, KITAP
- **Pendidikan (3):** NPSN, Akreditasi, Beasiswa
- **Kesehatan (3):** BPJS Kesehatan, JKN, Farmasi
- **Lingkungan (2):** AMDAL, Izin Lingkungan
- **Pertahanan (2):** Nopol, Kepabeanan

#### 3.3 Automated JDIH Scraper
Fix the scraper that was running:
```bash
# scrapers/
# ├── jdih_kemenaker.py       # Kemnaker website scraper
# ├── jdih_atrbpn.py          # ATR/BPN scraper
# ├── pdf_processor.py        # PDF → text extraction
# └── run_scraper.py          # Orchestrate all scrapers
```
- Verify PDFs are in `data/documents/pdfs/`
- Parse PDFs → extract text → chunk → embed → store
- Check `scraping_report.json` for status

---

### PHASE 4: USER AUTHENTICATION (3-4 days)
*"Add user accounts with Supabase"*

#### 4.1 Supabase Setup
```typescript
// frontend/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

#### 4.2 Auth Flow
```
/auth/login          → Email + password login
/auth/register       → Sign up
/auth/callback       → OAuth callback (Google, GitHub)
/auth/logout         → Sign out
```

#### 4.3 Protected Features
- Save searches → Supabase `saved_searches` table
- Bookmarks → Supabase `bookmarks` table
- Search history → Supabase `search_history` table (synced)
- User preferences → Supabase `user_preferences` table

#### 4.4 Backend Auth Middleware
```python
# api/auth.py
from supabase import create_client

@router.get("/me")
async def get_current_user(x_api_key: str = Header(...)):
    user = supabase.auth.get_user(x_api_key)
    return {"user_id": user.id, "email": user.email}
```

---

### PHASE 5: SEARCH ENGINE UPGRADE (2-3 days)
*"Make search actually good"*

#### 5.1 Hybrid Search (BM25 + Vector)
Current: TF-IDF only → upgrade to BM25 + semantic vector
```python
# src/retrieval/hybrid_search.py
class HybridSearch:
    def __init__(self, alpha=0.7):
        self.alpha = alpha  # weight for vector score
    
    def retrieve(self, query, top_k=10):
        bm25_scores = self.bm25.search(query)      # ← new
        vector_scores = self.vector.search(query)  # ← existing
        combined = self.alpha * vector_scores + (1-self.alpha) * bm25_scores
        return sorted(combined, key=lambda x: x['score'], reverse=True)
```

#### 5.2 Query Expansion
Current: simple → upgrade to:
```python
# src/retrieval/query_expander.py
class QueryExpander:
    """
    Indonesian query expansion:
    'biaya sim a' → ['biaya pembuatan SIM A', 'tarif SIM kelas A', ...]
    """
    def expand(self, query: str) -> list[str]:
        # Use Groq to generate query variations
        prompt = f"Ekpansi query印尼语: {query}"
        return groq.generate(prompt).split('\n')
```

#### 5.3 Reranking with Cross-Encoder
```python
# src/retrieval/reranker.py
class Reranker:
    """
    Cross-encoder reranking for better relevance.
    Re-rank top-50 results using cross-encoder model.
    """
    def rerank(self, query: str, candidates: list[Doc], top_k=10):
        # Use ms-marco-MiniLM-L-6-v2 or Indo伯特
        scores = cross_encoder.predict([(query, doc.text) for doc in candidates])
        return sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:top_k]
```

#### 5.4 Faceted Navigation
- Build `GET /documents/facets` endpoint → returns available filter values
- Frontend: show document counts per jenis/status/instansi
- Click facet → auto-apply filter

---

### PHASE 6: ADVANCED FEATURES (4-5 days)
*"Polish and differentiate"*

#### 6.1 Document Timeline View
```
┌──────────────────────────────────────────────────┐
│ UU 23/2006 (Admin Kependudukan)                  │
│ ├─ Amend: UU 24/2013 ─────────────────┐           │
│ │                                   │ 2013       │
│ └─ Amend: UU 9/2019 ─────────────────┘           │
│                                      │ 2019       │
└──────────────────────────────────────────────────┘
```
- Track which law amends which
- Visual timeline of amendments
- "Related laws" section

#### 6.2 Citation Generator
```python
# api/citations.py
FORMATS = {
    "apa7": "Republik Indonesia. ({tahun}). {jenis} Nomor {nomor} Tahun {tahun} tentang {judul}.",
    "bluebook": "{jenis} No. {nomor}/{tahun} tentang {judul} (Indon.)",
    "legal": "{jenis} {nomor} Tahun {tahun} (Indonesia)",
    "mla9": "Republik Indonesia. \"{judul}.\" {jenis} No. {nomor}, {tahun}.",
}
```

#### 6.3 Export & Share
- Share result as: link, citation, JSON, PDF
- Copy citation in chosen format
- Generate shareable URL with pre-filled query

#### 6.4 Performance Dashboard
```
/admin/analytics/page.tsx  → Already exists, needs real data
- Query volume chart (recharts)
- Response time histogram
- Error rate tracker
- Top queries
- Popular documents
```

#### 6.5 Mobile PWA
- Service Worker for offline reading of cached docs
- Install prompt
- Background sync
- Push notifications for new laws in user's area

---

### PHASE 7: DEPLOYMENT & MONITORING (2-3 days)
*"Go to production"*

#### 7.1 CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
- lint (ruff)
- type-check (mypy)
- test (pytest)
- build (docker)
- deploy ( Railway / Fly.io )
```

#### 7.2 Monitoring Stack
```
Sentry      → Error tracking (frontend + backend)
UptimeRobot → Ping monitoring every 5 min
Grafana     → Custom dashboard (query volume, latency)
```

#### 7.3 Deployment Config
```
Frontend  → Vercel (next build)
Backend   → Railway or Google Cloud Run
Vector DB  → ChromaDB Cloud OR self-hosted
Domain    → indogovrag.com (optional)
SSL       → Auto (Vercel + Railway)
```

---

## 🗂️ DETAILED TASK BREAKDOWN

### By File (What Needs to Change)

#### Backend Files to Create:
```
api/
├── search.py              ← NEW: /documents/search endpoint
├── citations.py           ← NEW: citation generator
├── auth.py                ← NEW: Supabase auth middleware
└── facets.py              ← NEW: /documents/facets endpoint
```

#### Backend Files to Fix:
```
api/main.py                ← Fix: ensure CSRF on all POST
src/rag/pipeline.py        ← Fix: Unicode encoding, ChromaDB path
src/retrieval/vector_search.py ← Fix: ensure all 18 docs indexed
scripts/reindex_all.py     ← NEW: bulk reindex script
scripts/check_dataset.py   ← Already exists, run it
```

#### Frontend Files to Create:
```
frontend/app/search/
├── components/
│   └── DocumentDetail.tsx ← NEW: full document view page
├── page.tsx                ← Fix: connect to real API
frontend/app/auth/
├── login/page.tsx          ← NEW
├── register/page.tsx       ← NEW
└── callback/page.tsx      ← NEW
frontend/lib/
├── supabase.ts             ← NEW
├── searchApi.ts            ← NEW: API client for search
└── citations.ts            ← NEW: client-side citation formatter
```

#### Frontend Files to Fix:
```
frontend/app/search/page.tsx           ← Connect to backend
frontend/app/search/components/        ← All should work end-to-end
frontend/app/components/DocumentManager.tsx ← Already fixed (port 8000)
```

---

## 📅 IMPLEMENTATION ORDER (Priority)

### Week 1: Fix & Stabilize
| # | Task | Files | Hours | Priority |
|---|------|-------|-------|----------|
| 1 | Fix RAG pipeline Unicode | `src/rag/pipeline.py` | 1 | P0 |
| 2 | Reindex all 18 documents | `scripts/reindex_all.py` | 2 | P0 |
| 3 | Test `/query` endpoint | - | 0.5 | P0 |
| 4 | Build `/documents/search` endpoint | `api/search.py` | 3 | P0 |
| 5 | Connect search page to API | `app/search/page.tsx` | 2 | P0 |
| 6 | Add document cards rendering | `SearchResultCard.tsx` | 1 | P1 |

### Week 2: Content & Quality
| # | Task | Files | Hours | Priority |
|---|------|-------|-------|----------|
| 7 | Verify scraper output | `scrapers/`, `data/documents/` | 1 | P0 |
| 8 | Fix scraper if needed | `scrapers/jdih_*.py` | 2 | P1 |
| 9 | Add 10 more documents | `data/documents/` | 8 | P1 |
| 10 | Validate all docs indexed | `scripts/validate_index.py` | 1 | P1 |

### Week 3: Search Engine
| # | Task | Files | Hours | Priority |
|---|------|-------|-------|----------|
| 11 | BM25 hybrid search | `src/retrieval/hybrid_search.py` | 3 | P1 |
| 12 | Query expansion | `src/retrieval/query_expander.py` | 2 | P1 |
| 13 | Cross-encoder reranking | `src/retrieval/reranker.py` | 3 | P1 |
| 14 | Faceted navigation | `api/facets.py`, frontend | 2 | P1 |

### Week 4: Auth & Polish
| # | Task | Files | Hours | Priority |
|---|------|-------|-------|----------|
| 15 | Supabase setup | `frontend/lib/supabase.ts` | 2 | P1 |
| 16 | Auth pages | `frontend/app/auth/` | 3 | P1 |
| 17 | Saved searches | `api/auth.py`, DB tables | 2 | P2 |
| 18 | Export/Share | frontend | 2 | P2 |
| 19 | Citation generator | `api/citations.py` | 2 | P2 |

### Week 5: Deploy
| # | Task | Files | Hours | Priority |
|---|------|-------|-------|----------|
| 20 | CI/CD pipeline | `.github/workflows/` | 2 | P1 |
| 21 | Sentry monitoring | `api/main.py` + frontend | 1 | P1 |
| 22 | Deploy frontend to Vercel | - | 1 | P0 |
| 23 | Deploy backend to Railway | - | 1 | P0 |
| 24 | Uptime monitoring | UptimeRobot | 0.5 | P1 |

**Total: ~43 hours across 5 weeks**

---

## 🔧 TECHNICAL NOTES

### ChromaDB on Windows
```python
# Problem: ChromaDB on Windows with non-ASCII paths
# Solution:
persist_dir = Path("data/vector_db/chroma").as_posix()
# or
persist_dir = str(Path("data/vector_db/chroma").resolve()).replace("\\", "/")
client = chromadb.PersistentClient(path=persist_dir)
```

### Groq API on Windows
```python
# Problem: GROQ_API_KEY not loading on Windows
# Solution:
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
api_key = os.getenv("GROQ_API_KEY")
```

### Next.js 16 on Windows
```bash
# Problem: Multiple lockfiles warning
# Solution: Already warned in console — not blocking, just a warning
# Option: remove root package-lock.json if not needed
```

### Frontend-backend Communication
```typescript
// All API calls go to backend (port 8000), not directly to Groq
// Frontend → /query → FastAPI → Groq
// Frontend never calls Groq directly (API key stays on backend)
```

---

## 📈 SUCCESS METRICS

| Metric | Now | v1.0-beta | v1.0-stable |
|--------|-----|-----------|-------------|
| Documents indexed | 3 chunks | 50+ docs | 100+ docs |
| Search quality | Basic | BM25+vector hybrid | + reranking |
| Auth | None | Supabase | Full user system |
| Response time | ~2-5s | <2s | <1s |
| Uptime | Dev only | 99% | 99.9% |
| Monitoring | None | Sentry | Full stack |
| Mobile | Responsive | PWA | PWA + offline |
| Export | None | PDF, JSON | PDF, JSON, Citation |
| Security | A- (90%) | A (92%) | A+ (95%) |

---

## 🎯 QUICK START COMMANDS

```bash
# Fix and start
cd IndoGovRAG
make dev                          # Start backend (port 8000)
# Terminal 2:
cd frontend && npm run dev        # Start frontend (port 3000)

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"syarat membuat KTP"}'

# Reindex documents
python scripts/reindex_all.py

# Check vector DB
curl http://localhost:8000/stats

# Run scraper
python scrapers/run_scraper.py

# Run tests
make test

# Docker
make docker-build && make docker-up
```

---

## 📁 KEY FILES REFERENCE

| Purpose | File |
|---------|------|
| Backend entry | `api/main.py` |
| RAG core | `src/rag/pipeline.py` |
| LLM (Groq) | `src/llm/groq_llm.py`, `src/llm/multi_tier_llm.py` |
| Vector search | `src/retrieval/vector_search.py` |
| BM25 search | `src/retrieval/bm25_search.py` |
| Query expansion | `src/retrieval/query_expander.py` |
| Re-ranker | `src/retrieval/reranker.py` |
| Frontend main | `frontend/app/page.tsx` |
| Search page | `frontend/app/search/page.tsx` |
| Search store | `frontend/app/lib/searchStore.ts` |
| Design system | `frontend/app/globals.css` |
| Providers | `frontend/app/providers.tsx` |
| Documents | `data/documents/` |
| Vector DB | `data/vector_db/chroma/` |
| Scripts | `scripts/`, `scrapers/` |

---

**Built with ❤️ for Indonesia 🇮🇩**
**Making government information accessible to everyone!**