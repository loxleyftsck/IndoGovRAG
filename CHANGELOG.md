# 📝 Changelog

All notable changes to IndoGovRAG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Week 1 - In Progress)
- Project structure standardization
- Data collection pipeline (planned)
- Indonesian text preprocessing (planned)
- Vector store setup (planned)

## [0.1.0] - 2024-12-17

### ✅ Week 0 Foundation - COMPLETE

#### Added
- **Monitoring Infrastructure**
  - Local Gemini quota tracker (`src/monitoring/gemini_quota_tracker.py`)
  - API wrapper with auto-retry (`src/monitoring/gemini_wrapper.py`)
  - Demo script and comprehensive documentation
  
- **Baseline Evaluation Dataset**
  - 10-question Indonesian gov docs dataset
  - Validation script and quality checks
  - Question categories: factual lookup, reasoning, summarization, edge cases
  
- **Embedding Model Selection**
  - Benchmarking framework for Indonesian NLP
  - Chose multilingual-e5-base (768-dim, 80-90% Hit@1)
  - Alternatives documented (LaBSE, IndoBERT)
  
- **Data Source Audit**
  - Verified access to JDIH network (8+ ministry portals)
  - Collection strategy for 50-100 initial documents
  - Quality checklist and validation criteria
  
- **Experiment Tracking**
  - Local JSON-based tracker (W&B alternative)
  - Side-by-side experiment comparison
  - Zero-cost monitoring solution
  
- **LLM Fallback System**
  - Multi-tier: Gemini Pro → Flash → Local (optional)
  - Automatic quota-aware failover
  - Statistics tracking
  
- **Documentation** (8 comprehensive guides)
  - Gemini Quota Guide
  - Data Source Audit
  - Embedding Choice Rationale
  - LLM Fallback Strategy
  - Experiment Tracking Guide
  - Data Quality Checklist
  - Baseline Dataset Summary
  - Project Structure

#### Project Setup
- Python project structure (src/, data/, docs/, tests/)
- Requirements.txt with all dependencies
- Configuration management (config.env)
- MIT License
- README.md with project overview
- .gitignore for Python projects

#### Metrics
- **Time Invested**: 15 hours
- **Total Cost**: $0.00
- **Files Created**: 25+
- **Lines of Code**: ~1,500
- **Documentation Pages**: 8
- **Test Coverage**: 0% (Week 1 target)

### Technical Decisions
- **Embedding Model**: multilingual-e5-base
- **Vector DB**: ChromaDB (file-based, local)
- **LLM Primary**: Gemini Pro (free tier)
- **LLM Fallback**: Gemini Flash (separate quota)
- **Experiment Tracking**: Local JSON (no external services)
- **Deployment**: Vercel Serverless (planned, zero-cost)

### Week 0 Deliverables
- [x] Validated tech stack
- [x] Baseline metrics (10-question dataset)
- [x] Monitoring infrastructure
- [x] Data sources verified
- [x] Quality standards defined
- [x] Fallback strategy
- [x] Documentation complete

---

## Roadmap

### Week 1 (In Progress) - Secure RAG Implementation
- [ ] Data collection from JDIH (50-100 PDFs)
- [ ] Indonesian text preprocessing
- [ ] PII detection & redaction
- [ ] Document chunking (512 tokens)
- [ ] Vector store setup (ChromaDB)
- [ ] Basic RAG query interface
- [ ] Unit tests

### Week 2 - Evaluation Framework
- [ ] RAGAS integration
- [ ] 100-question expanded dataset
- [ ] Baseline benchmark
- [ ] Metric dashboard

### Week 3 - Optimization
- [ ] Hybrid search (vector + BM25)
- [ ] Reranking implementation
- [ ] A/B testing (chunk sizes, top-K)

### Week 4 - Monitoring & UI
- [ ] Streamlit dashboard
- [ ] Cost tracking
- [ ] Performance monitoring

### Week 5 - Deployment
- [ ] Vercel serverless deployment
- [ ] Production testing
- [ ] Blog post & documentation

---

**Full Version History**: [GitHub Releases](https://github.com/yourusername/indogovrag/releases)
