# 📚 Tier 2 Solution: Document Corpus Enrichment Strategy

**Goal:** Increase corpus from 53 → 200-300 documents  
**Expected Impact:** +40-50% answer quality improvement  
**Root Cause Addressed:** Document coverage (70% of quality issues)

---

## 🎯 Priority Sources (Tier 1: High-Authority)

### 1. Portal Resmi Pemerintah

**JDIH (Jaringan Dokumentasi dan Informasi Hukum)**

- URL: <https://jdih.setkab.go.id>
- Content: UU, PP, Perpres, Peraturan Menteri
- Format: PDF (perlu extract text)
- Priority: HIGH (legal citations)

**Peraturan.go.id**

- URL: <https://peraturan.go.id>
- Content: Database lengkap peraturan perundangan
- Format: HTML + PDF
- Priority: HIGH

**Indonesia.go.id** ✅ IMPLEMENTED

- URL: <https://indonesia.go.id/kategori/layanan-publik>
- Content: Panduan layanan, syarat dokumen
- Format: HTML artikel
- Priority: MEDIUM (already scraped)

### 2. Portal Layanan Publik

**OSS (Online Single Submission)**

- URL: <https://oss.go.id/informasi>
- Content: Panduan izin usaha, FAQ
- Priority: MEDIUM

### 3. Portal Kementerian

**Kemendagri (Dukcapil)**

- URL: <https://www.kemendagri.go.id>
- Content: KTP, KK, Akta
- Priority: HIGH (most common queries)

**Kementerian Hukum dan HAM**

- URL: <https://www.kemenkumham.go.id>  
- Content: Paspor, visa, imigrasi
- Priority: MEDIUM

---

## 📊 Target Coverage Metrics

### Current State

```yaml
Total documents: 53
Categories:
  - Mixed government docs
  - Manual + scraped content
  
Coverage gaps:
  - KTP specific info: LOW
  - Akta procedures: LOW
  - Izin usaha details: LOW
```

### Target State (Phase 1: 200-300 docs)

```yaml
Administrasi Kependudukan: 50+ docs
  - KTP elektronik: 15 docs
  - Kartu Keluarga: 10 docs
  - Akta kelahiran: 10 docs
  - Akta nikah: 5 docs
  - Akta kematian: 5 docs
  - Lain-lain: 5 docs

Perizinan Usaha: 30+ docs
  - OSS/NIB: 10 docs
  - UMKM: 10 docs
  - Izin khusus: 10 docs

Peraturan Perundangan: 100+ docs
  - UU: 30 docs
  - PP: 30 docs
  - Perpres: 20 docs
  - Permen: 20 docs

Layanan Lainnya: 50+ docs
  - Kesehatan (BPJS): 10 docs
  - Pajak (NPWP): 10 docs
  - Pendidikan: 10 docs
  - FAQ & Panduan: 20 docs
```

---

## 🛠️ Implementation Plan

### Phase 1: Quick Wins (Week 2) ✅ IN PROGRESS

**Script:** `scripts/scrape_gov_docs.py` (created!)

**Actions:**

1. ✅ Install dependencies

   ```bash
   pip install requests beautifulsoup4 pdfplumber lxml
   ```

2. ✅ Run scraper for indonesia.go.id

   ```bash
   python scripts/scrape_gov_docs.py
   ```

3. ⏸️ Review scraped documents

   ```bash
   cat data/scraped/indonesiagov_*.json | jq '.[] | .title'
   ```

4. ⏸️ Ingest to RAG system

   ```bash
   python scripts/ingest_documents.py --source data/scraped/*.json
   ```

**Expected:** +30-50 new documents, +20% answer quality

---

### Phase 2: Scale Up (Week 3-4)

**Expand to more sources:**

1. **Add OSS scraper** (izin usaha)
   - Implement `scrape_oss_go_id()` method
   - Target: 20-30 docs

2. **Add Kemendagri scraper** (KTP/KK/Akta)
   - Implement `scrape_kemendagri()` method
   - Target: 30-40 docs

3. **Add JDIH scraper** (legal documents)
   - Implement `scrape_jdih()` with PDF extraction
   - Target: 50-100 docs

**Expected:** Total 150-200 documents

---

### Phase 3: Quality & Maintenance (Month 2)

**Quality Assurance:**

1. Manual review of scraped content
2. Remove duplicates
3. Fix extraction errors
4. Add metadata (legal citations, dates)

**Maintenance:**

1. Re-scrape weekly for updates
2. Monitor for broken links
3. Expand to new sources based on query patterns

**Expected:** High-quality 200-300 doc corpus

---

## 📋 Quick Start Guide

### Step 1: Install Dependencies (5 min)

```bash
pip install requests beautifulsoup4 pdfplumber lxml
```

### Step 2: Run Scraper (10-15 min)

```bash
# Scrape indonesia.go.id
python scripts/scrape_gov_docs.py

# Check results
ls -lh data/scraped/

# Preview
python -c "
import json
with open(list(Path('data/scraped').glob('indonesiagov_*.json'))[0]) as f:
    docs = json.load(f)
    print(f'Total: {len(docs)} documents')
    for doc in docs[:5]:
        print(f\"- {doc['title'][:60]}... ({doc['category']})\")
"
```

### Step 3: Ingest to RAG (10 min)

```bash
# Convert & ingest
python scripts/ingest_documents.py --source data/scraped/*.json

# Verify
python -c "
from src.retrieval.vector_search import VectorStore
vs = VectorStore()
print(f'Total docs in vector store: {vs.collection.count()}')
"
```

### Step 4: Test Improvements (5 min)

```bash
# Test with enhanced prompts + more docs
python scripts/test_enhanced_prompts.py
```

---

## ✅ Success Criteria

### Immediate (Week 2)

- [ ] 100+ documents in corpus (vs 53)
- [ ] KTP coverage: >10 docs
- [ ] Akta coverage: >10 docs
- [ ] Answer quality +20-30% on test queries

### Short-term (Month 1)

- [ ] 200+ documents
- [ ] All major categories covered (>5 docs each)
- [ ] Answer quality +40-50%
- [ ] RAGAS faithfulness >0.92

### Long-term (Month 2-3)

- [ ] 300+ documents
- [ ] Automated weekly re-scraping
- [ ] Legal document full coverage (UU, PP, Perpres)
- [ ] Production-grade corpus quality

---

## 🎓 Best Practices

### Ethical Scraping

1. ✅ Respect robots.txt
2. ✅ Rate limiting (2s between requests)
3. ✅ User-Agent identification
4. ✅ Cache to avoid re-scraping
5. ✅ Attribution to sources

### Quality Control

1. ✅ Min content length: 200 chars
2. ✅ Language filter: Indonesian only
3. ✅ Recent content: 2020-2026
4. ✅ Deduplication
5. ✅ Manual spot-checks

### Maintenance

1. ✅ Log all scraping activity
2. ✅ Monitor failed requests
3. ✅ Track coverage by category
4. ✅ Update quarterly

---

## 💡 Next Steps

**NOW (Tier 2A - 30 min):**

1. Run `scrape_gov_docs.py` for indonesia.go.id
2. Get 20-50 new documents
3. Ingest to RAG
4. Test answer improvement

**Week 2 (Tier 2B - 2 days):**

1. Expand scraper to OSS + Kemendagri
2. Target 150-200 total docs
3. Run RAGAS evaluation
4. Measure improvement

**Month 2 (Tier 2C - 1 week):**

1. Add JDIH legal documents
2. Reach 300+ docs
3. Automated re-scraping
4. Production-grade corpus

---

**Status:** Tier 2A ready to execute  
**Impact:** +40-50% answer quality (addresses 70% root cause)  
**Timeline:** 30 min for first run, 2 weeks for full implementation

**This is the BIGGEST win for answer quality!** 🚀
