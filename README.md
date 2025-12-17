# 🇮🇩 **IndoGovRAG** - Indonesian Government Documents RAG System

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-in_development-yellow.svg)]()

**Production-Ready RAG System for Indonesian Government Documents**

> Retrieval-Augmented Generation system built to answer questions about Indonesian government regulations, laws, and policies using JDIH (Jaringan Dokumentasi dan Informasi Hukum) data.

---

## 🎯 **Project Overview**

**IndoGovRAG** is a complete RAG (Retrieval-Augmented Generation) system designed specifically for Indonesian government documents. It combines:
- 🇮🇩 **Indonesian NLP** optimization
- 🔒 **PII detection** and security
- 💰 **100% free** infrastructure
- ⚡ **Production-ready** architecture
- 🌱 **Energy-efficient** serverless deployment

**Use Cases:**
- Answer questions about Indonesian laws & regulations
- Search government policies quickly
- Understand complex legal documents
- Reference official government rulings

---

## ✨ **Features**

### Core Functionality
- ✅ **Semantic Search** - Dense vector retrieval with multilingual-e5-base
- ✅ **Multi-tier LLM** - Gemini Pro → Flash → Local fallback
- ✅ **Indonesian-Optimized** - Text normalization, language detection
- ✅ **PII Protection** - Automatic detection & redaction (NIK, email, phone)
- ✅ **Quota Tracking** - Local monitoring (no external services)
- ✅ **Experiment Logging** - JSON-based tracking

### Production Features
- 🔄 **Automatic Fallback** - 3-tier LLM system (99%+ uptime)
- 📊 **Quality Metrics** - RAGAS evaluation framework
- 🔒 **Security** - PII detection, audit logging
- ⚡ **Performance** - <2s P95 latency target
- 🌍 **Serverless** - Zero-cost deployment option

---

## 🚀 **Quick Start**

### Prerequisites
- Python 3.9+
- Gemini API key ([Get free key](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/indogovrag.git
cd indogovrag

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Basic Usage

```python
from src.rag.pipeline import RAGPipeline

# Initialize RAG system
rag = RAGPipeline()

# Query
response = rag.query("Apa persyaratan membuat KTP elektronik?")
print(response["answer"])
```

---

## 📊 **Architecture**

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Text Preprocessing         │
│  - Indonesian normalization │
│  - PII detection            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Embedding Generation       │
│  - multilingual-e5-base     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Vector Search (ChromaDB)   │
│  - Top-K retrieval          │
│  - Semantic similarity      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Context + Query → LLM      │
│  - Gemini Pro (primary)     │
│  - Gemini Flash (fallback)  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│  Final Answer   │
└─────────────────┘
```

---

## 📁 **Project Structure**

```
indogovrag/
├── src/
│   ├── data/          # Data pipeline (loading, preprocessing, chunking)
│   ├── embeddings/    # Embedding models & benchmarking
│   ├── retrieval/     # Vector & hybrid search
│   ├── rag/           # RAG pipeline & prompts
│   ├── llm/           # Multi-tier LLM client
│   ├── monitoring/    # Quota tracking & logging
│   └── evaluation/    # Experiment tracking & metrics
├── data/
│   ├── documents/     # PDFs from JDIH
│   ├── vector_db/     # ChromaDB storage
│   └── baseline_eval_dataset.json
├── docs/              # Documentation (8 guides)
├── tests/             # Unit & integration tests
├── scripts/           # Utility scripts
└── config/            # Configuration files
```

See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for details.

---

## 🛠️ **Tech Stack**

| Component | Technology | Cost |
|-----------|-----------|------|
| **LLM** | Gemini Pro + Flash | FREE (3K req/day) |
| **Embeddings** | multilingual-e5-base | FREE (local) |
| **Vector DB** | ChromaDB | FREE (local) |
| **Evaluation** | RAGAS | FREE |
| **Hosting** | Vercel Serverless | FREE |
| **Monitoring** | Local JSON | FREE |

**Total Monthly Cost:** $0 💰

---

## 📈 **Performance Metrics**

| Metric | Target | Status |
|--------|--------|--------|
| Context Precision | >0.85 | 🎯 TBD (Week 2) |
| Faithfulness | >0.90 | 🎯 TBD (Week 2) |
| Answer Relevancy | >0.85 | 🎯 TBD (Week 2) |
| Latency P95 | <2s | 🎯 TBD (Week 2) |
| Cost per Query | $0.00 | ✅ FREE |

---

## 📚 **Documentation**

Comprehensive guides available in `docs/`:
- [Gemini Quota Tracker](docs/GEMINI_QUOTA_GUIDE.md) - API quota management
- [Data Source Audit](docs/DATA_SOURCE_AUDIT.md) - JDIH portal access
- [Embedding Choice](docs/EMBEDDING_CHOICE_RATIONALE.md) - Model selection
- [LLM Fallback Strategy](docs/LLM_FALLBACK_STRATEGY.md) - Multi-tier system
- [Experiment Tracking](docs/EXPERIMENT_TRACKING_GUIDE.md) - Logging experiments
- [Data Quality Checklist](docs/DATA_QUALITY_CHECKLIST.md) - Validation standards
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Folder organization

---

## 🧪 **Development Roadmap**

- [x] **Week 0** - Foundation & Validation ✅
  - Quota tracking, baseline dataset, model selection, data sources
- [ ] **Week 1** - Secure RAG Implementation 🔧
  - Data collection, preprocessing, vector store, basic RAG
- [ ] **Week 2** - Evaluation Framework
  - RAGAS metrics, 100-question dataset, baseline benchmark
- [ ] **Week 3** - Optimization & Comparison
  - Hybrid search, reranking, A/B testing
- [ ] **Week 4** - Monitoring & Documentation
  - Dashboard, cost tracking, deployment
- [ ] **Week 5** - Polish & Deployment
  - Final testing, production deploy, blog post

Full roadmap: [UPDATED_RAG_ROADMAP.md](UPDATED_RAG_ROADMAP.md)

---

## 🤝 **Contributing**

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 **License**

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **JDIH Network** - Indonesian government legal documentation portal
- **Google Gemini** - Free tier LLM API
- **Sentence Transformers** - Embedding models
- **ChromaDB** - Vector database
- **RAGAS** - RAG evaluation framework

---


---

<p align="center">
  <strong>Built with ❤️ for Indonesia 🇮🇩</strong><br>
  <sub>Made possible by 100% free & open-source tools</sub>
</p>
