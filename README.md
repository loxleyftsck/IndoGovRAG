# 🇮🇩 IndoGovRAG - Production-Grade Indonesian Government RAG System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Enterprise Grade](https://img.shields.io/badge/Enterprise-85%25-success.svg)](https://github.com/loxleyftsck/IndoGovRAG)

> **Enterprise-grade RAG system for Indonesian government regulations with production observability, safety controls, and cost optimization**

🎯 **Status:** Beta Ready (Phase 1.5) | 💰 **Optimized Cost:** -41% | ⚡ **Latency:** -32% | 🛡️ **Security:** Grade A-

---

## 🚀 **What's New - Phase 1.5 Optimization**

**Latest:** January 2026 - Cost & Latency Optimization Complete

- ✅ **30% Token Reduction** - LLMLingua compression (Config #8)
- ✅ **52% Cache Hit Rate** - Semantic caching with Redis
- ✅ **41% Cost Savings** - From $0.0029 to $0.0017 per request
- ✅ **32% Faster** - P95 latency reduced from 15.3s to 10.4s
- ✅ **Quality Maintained** - Only 2.1% faithfulness degradation

**Ready for beta deployment with gradual rollout (10% → 50% → 100%)**

---

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Phase 1.5 Optimizations](#phase-15-optimizations)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Monitoring & Observability](#monitoring--observability)
- [Performance Metrics](#performance-metrics)

---

## ✨ Features

### **Phase 1: Enterprise Hardening (85% Complete)**

**Observability & Monitoring:**

- ✅ Distributed tracing (OpenTelemetry + Jaeger)
- ✅ Prometheus metrics (latency, cost, quality, error rates)
- ✅ Grafana dashboards (RAG pipeline, LLM performance, cache efficiency)
- ✅ Structured logging (JSON logs, correlation IDs)

**Safety & Deployment:**

- ✅ Canary deployment (gradual traffic shifting)
- ✅ Automatic rollback (error threshold triggers)
- ✅ Circuit breakers (LLM rate limit protection)
- ✅ Health checks (readiness/liveness probes)

**Governance & Compliance:**

- ✅ Audit trail (privacy-safe query hashing)
- ✅ User feedback collection (ratings + comments)
- ✅ PII detection placeholder (ready for integration)
- ✅ Rate limiting (per-user quotas)

### **Phase 1.5: Cost & Latency Optimization (Config #8)**

**Context Compression:**

- ✅ LLMLingua integration (30% token reduction)
- ✅ Legal keyword protection (Pasal, UU, numbers preserved)
- ✅ Graceful fallback on errors
- ✅ <500ms compression latency

**Semantic Caching:**

- ✅ Query embedding similarity (threshold 0.95)
- ✅ Redis backend (7-day TTL)
- ✅ False positive detection
- ✅ Hit/miss tracking

**Gradual Rollout:**

- ✅ Feature flags (0% → 10% → 50% → 100%)
- ✅ A/B testing ready
- ✅ Emergency killswitch
- ✅ Automatic rollback on quality drops

### **Core RAG Capabilities:**

- ✅ Semantic Search - Vector similarity (ChromaDB)
- ✅ Hybrid Retrieval - BM25 + Vector fusion
- ✅ LLM Generation - Gemini Flash with multi-tier fallback
- ✅ Query Expansion - Automatic enhancement
- ✅ Result Re-ranking - LLM-based relevance scoring

---

## 🚀 Quick Start

### **Prerequisites:**

- Python 3.11+
- Redis (for caching) - optional, falls back to memory
- Git

### **Installation:**

```bash
# 1. Clone repository
git clone https://github.com/loxleyftsck/IndoGovRAG.git
cd IndoGovRAG

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env and add:
#   GEMINI_API_KEY=your_key_here
#   REDIS_HOST=localhost (optional)

# 4. Load data
python scripts/load_sample_docs.py

# 5. Start backend
python api/main.py
# Server: http://localhost:8000

# 6. Test
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Apa itu KTP elektronik?"}'
```

### **With Optimizations (Phase 1.5):**

```bash
# Enable optimizations via environment variable
export OPTIMIZATION_ROLLOUT_PCT=100  # 0-100%

# Or edit config/optimization_config.py
# OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = 10
```

---

## ⚡ Phase 1.5 Optimizations

### **Configuration: Config #8 (Beta Default)**

```yaml
compression:
  enabled: true
  ratio: 0.7  # Keep 70% of tokens
  
caching:
  enabled: true
  threshold: 0.95  # 95% similarity
  ttl_days: 7
  
rollout:
  percentage: 0  # Start at 0%, increase gradually
```

### **Performance Improvements:**

| Metric | Baseline | Config #8 | Improvement |
|--------|----------|-----------|-------------|
| **P95 Latency** | 15.3s | 10.4s | **-32%** ✅ |
| **Cost/Request** | $0.0029 | $0.0017 | **-41%** ✅ |
| **Faithfulness** | 0.780 | 0.763 | -2.1% ✅ |
| **Cache Hit Rate** | 0% | 52% | **NEW** ✅ |

### **Gradual Rollout Plan:**

- **Week 1:** 10% traffic (canary testing)
- **Week 2:** 50% traffic (validation)
- **Week 3:** 100% traffic (full deployment)

**Safety:** Automatic rollback if error >10%, latency >15s, or quality <0.74

---

## 🏗️ Architecture

### **System Overview:**

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  API Layer (FastAPI)                │
│  - Rate limiting                    │
│  - Authentication (planned)         │
│  - Traffic splitting (canary)       │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Optimization Layer (Phase 1.5)     │
│  - Semantic cache (Redis)           │
│  - Context compression (LLMLingua)  │
│  - Feature flags                    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  RAG Pipeline                       │
│  1. Query expansion                 │
│  2. Hybrid retrieval (BM25+Vector)  │
│  3. LLM re-ranking                  │
│  4. Context compression (optional)  │
│  5. LLM generation (Gemini Flash)   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Observability (Phase 1)            │
│  - Tracing (Jaeger)                 │
│  - Metrics (Prometheus)             │
│  - Dashboards (Grafana)             │
│  - Audit logging                    │
└─────────────────────────────────────┘
```

### **Directory Structure:**

```
IndoGovRAG/
├── api/                  # FastAPI backend
│   └── main.py          # Endpoints + canary deployment
├── src/
│   ├── rag/             # RAG pipeline
│   ├── compression/     # Context compression (BET-002)
│   ├── caching/         # Semantic cache (BET-003)
│   ├── monitoring/      # Observability (Phase 1)
│   ├── audit/           # Audit trail
│   └── feedback/        # User feedback
├── config/
│   └── optimization_config.py  # Config #8 (BET-001)
├── tests/               # Test suite (80%+ coverage)
├── grafana/             # Monitoring dashboards
│   └── dashboards/
│       ├── rag_pipeline.json
│       ├── cache_performance.json
│       └── optimization_health.json
└── docs/                # Documentation
    └── phase1.5/        # Phase 1.5 reports
```

---

## 📚 API Documentation

### **Base URL:** `http://localhost:8000`

### **Main Endpoints:**

#### **1. Query (Optimized)**

```http
POST /query
Content-Type: application/json

{
  "query": "Persyaratan membuat KTP?",
  "top_k": 3,
  "include_sources": true
}
```

**Response:**

```json
{
  "answer": "Berdasarkan UU No. 24 Tahun 2013...",
  "sources": ["doc_1", "doc_2"],
  "confidence": 0.85,
  "latency_ms": 10400,
  "metadata": {
    "variant": "optimized",
    "compressed": true,
    "cached": false,
    "compression_ratio": 0.68
  }
}
```

#### **2. Admin - Optimization Status**

```http
GET /admin/optimization/status
```

#### **3. Admin - Emergency Disable**

```http
POST /admin/optimization/disable
Authorization: Bearer <ADMIN_API_KEY>
```

#### **4. Health Check**

```http
GET /health
```

**Swagger Docs:** `http://localhost:8000/docs`

---

## 🛠️ Development

### **Setup:**

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest --cov=src

# Lint
ruff check .

# Type check
mypy .
```

### **Development Standards:**

See `DEVELOPER_STANDARDS.md`:

- ✅ Type hints 100% required
- ✅ Google-style docstrings
- ✅ 80%+ test coverage
- ✅ Security-first (input validation, rate limiting)

### **Running with Monitoring:**

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access:
# - Grafana: http://localhost:3001 (admin/admin)
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
```

---

## 🚢 Deployment

### **Production Deployment:**

```bash
# Using Docker
docker-compose up -d

# Environment variables
GEMINI_API_KEY=<key>
REDIS_HOST=<redis-url>
OPTIMIZATION_ROLLOUT_PCT=10  # Start at 10%
```

### **Staging:**

```bash
# Deploy to Fly.io
fly launch
fly deploy

# Or Railway
railway init
railway up
```

See `docs/DEPLOYMENT.md` for full guide.

---

## 📊 Monitoring & Observability

### **Grafana Dashboards:**

1. **RAG Pipeline Dashboard**
   - Query latency (P50/P95/P99)
   - Cost per request
   - Error rates
   - Quality metrics (faithfulness/relevancy)

2. **Optimization Health Dashboard** (Phase 1.5)
   - Traffic split (optimized vs baseline)
   - Cache hit rate
   - Compression success rate
   - Cost savings

3. **Cache Performance Dashboard**
   - Hit/miss ratio
   - False positive rate
   - Latency impact
   - Memory usage

### **Metrics Available:**

```python
# Prometheus metrics
indogovrag_query_latency_seconds{variant="optimized"}
indogovrag_query_total{status="success", variant="baseline"}
indogovrag_cache_hits_total
indogovrag_compression_ratio
indogovrag_cost_per_request_usd
```

### **Tracing:**

All requests traced with OpenTelemetry:

- Query flow visualization
- Span-level latency breakdown
- Error attribution

Access Jaeger UI: `http://localhost:16686`

---

## ⚡ Performance Metrics

### **Current Performance (Phase 1.5 Config #8):**

| Metric | Value | Status |
|--------|-------|--------|
| **P95 Latency** | 10.4s | ✅ -32% from baseline |
| **Cost/Request** | $0.0017 | ✅ -41% from baseline |
| **Faithfulness** | 0.763 | ✅ Within threshold (<5% drop) |
| **Cache Hit Rate** | 52% | ✅ Above 45% target |
| **Error Rate** | <2% | ✅ Below 10% threshold |
| **Test Coverage** | 80%+ | ✅ Meets standard |

### **Scalability:**

- **Current:** 10-20 beta users
- **Target (Phase 2):** 100+ concurrent users
- **Infrastructure:** Multi-tenant architecture planned

### **Cost Analysis:**

**Annual Savings (at 1000 requests/day):**

- Baseline: $1,058/year
- Optimized: $620/year
- **Savings: $438/year (41%)**

---

## 📖 Documentation

### **Core Docs:**

- `README.md` - This file
- `DEVELOPER_STANDARDS.md` - Code quality guidelines
- `ROADMAP.md` - Product roadmap

### **Phase 1 (Enterprise Hardening):**

- `docs/WEEK3_FINAL_COMPLETION.md` - Phase 1 summary (85% ready)
- `docs/FINAL_PROJECT_REPORT.md` - Enterprise readiness report
- `docs/ENTERPRISE_REALITY_CHECK_V2.md` - Multi-dimensional evaluation

### **Phase 1.5 (Optimization):**

- `docs/phase1.5/PHASE1_5_TUNING_REPORT.md` - Experiment results
- `docs/phase1.5/PHASE1_5_RESULTS_COMPARISON.md` - 18 configs compared
- `docs/roadmaps/POST_PHASE1_5_ROADMAP.md` - Beta rollout plan
- `docs/plans/OPERATIONAL_EXECUTION_PLAN.md` - Implementation tickets

### **Technical:**

- `docs/ARCHITECTURE.md` - System design
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/SECURITY.md` - Security practices

---

## 🎯 Project Goals

### **Mission:**

Provide production-grade RAG system for Indonesian government regulations with enterprise observability, cost optimization, and safety controls.

### **Target Users:**

- Indonesian citizens seeking government information
- Legal professionals researching regulations
- Government agencies automating citizen services
- Developers building civic tech applications

### **Success Criteria:**

**Phase 1 (Complete):**

- ✅ 85% enterprise readiness
- ✅ Full observability (tracing, metrics, dashboards)
- ✅ Canary deployment + rollback
- ✅ Audit trail + feedback collection

**Phase 1.5 (Current):**

- ✅ 40% cost reduction
- ✅ 30% latency reduction
- ✅ <5% quality degradation
- ✅ Beta deployment ready

**Phase 2 (Planned):**

- ⏳ Multi-tenancy support
- ⏳ Role-based access control (RBAC)
- ⏳ Encryption at rest
- ⏳ Scale to 100+ concurrent users

---

## 🛡️ Security

**Current Security Grade: A-** (Phase 1)

**Implemented:**

- ✅ Audit logging (privacy-safe hashing)
- ✅ Rate limiting (per-user quotas)
- ✅ Input validation
- ✅ CORS configuration
- ✅ Error message sanitization

**Planned (Phase 2):**

- ⏳ Authentication (OAuth 2.0)
- ⏳ RBAC (role-based permissions)
- ⏳ Encryption at rest
- ⏳ PII detection (active)
- ⏳ Prompt injection defense

See `SECURITY.md` for responsible disclosure.

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/BET-XXX-description`
3. **Follow** `DEVELOPER_STANDARDS.md`
4. **Write tests** (80%+ coverage required)
5. **Commit:** `git commit -m 'feat(module): description [BET-XXX]'`
6. **Push:** `git push origin feature/BET-XXX-description`
7. **Open** Pull Request

See `CONTRIBUTING.md` for detailed guide.

---

## 📊 Project Status

**Current Phase:** 1.5 (Cost & Latency Optimization)  
**Status:** Beta Ready  
**Grade:** 85% Enterprise Ready  
**Cost:** $0.00 development (free tier)  

**Recent Milestones:**

- ✅ January 2026: Phase 1.5 optimization complete
- ✅ December 2025: Phase 1 enterprise hardening (85%)
- ✅ Week 8: Production stability achieved
- ✅ Week 1-3: Core RAG pipeline

**Next Milestones:**

- ⏳ Week 1-2: Beta deployment (10% → 50% traffic)
- ⏳ Week 3-4: Full rollout (100% traffic)
- ⏳ Month 2-3: Phase 2 planning (multi-tenancy)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 👥 Team

**Developer:** loxleyftsck  
**Repository:** <https://github.com/loxleyftsck/IndoGovRAG>  
**Contact:** Open an issue for questions

---

## 🙏 Acknowledgments

- Google Gemini API
- ChromaDB (vector search)
- LLMLingua (compression)
- FastAPI (backend framework)
- OpenTelemetry + Prometheus + Grafana (observability)
- Indonesian Government (JDIH, Peraturan.go.id)

---

## 🌟 Star History

**⭐ Star this repo if you find it useful!**

**Production ready with enterprise features!** 🚀

---

**Latest Update:** Phase 1.5 Complete - January 2026  
**Next:** Beta Deployment with Config #8
