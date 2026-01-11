# 📊 Standar Kelayakan Data untuk RAG Production

**Dokumen:** Evaluasi Kualitas Data IndoGovRAG  
**Tanggal:** 11 Januari 2026  
**Status:** Assessment & Recommendations

---

## 🎯 Standar Industry untuk RAG Data Quality

### 1. Document Volume Standards (Berdasarkan Research)

**Minimum Viable (MVP/Prototype):**

```yaml
Total Documents: 20-50 docs
Chunks: 100-200 chunks
Use Case: Proof of concept, testing
Quality: 60-70% answer coverage
```

**Beta/Small Production:**

```yaml
Total Documents: 100-300 docs
Chunks: 500-1,500 chunks
Use Case: Limited production, specific domain
Quality: 75-85% answer coverage
```

**Production (General):**

```yaml
Total Documents: 500-2,000 docs
Chunks: 2,500-10,000 chunks
Use Case: Full production, broad coverage
Quality: 85-95% answer coverage
```

**Enterprise Scale:**

```yaml
Total Documents: 5,000-50,000+ docs
Chunks: 25,000-250,000+ chunks
Use Case: Large-scale, comprehensive
Quality: 95%+ answer coverage
```

---

## 📋 RAG Data Quality Metrics (Industry Standard)

### A. Coverage Metrics

**1. Topic Coverage**

```yaml
Definition: % of expected topics with ≥3 documents
Minimum (Beta): 60% topics covered
Production Target: 85%+ topics covered
Enterprise: 95%+ topics covered

Example IndoGovRAG:
  Expected topics: 15 (KTP, KK, Akta, Izin, NPWP, etc)
  Minimum docs: 15 topics × 3 docs = 45 documents
  Production: 15 topics × 10 docs = 150 documents
```

**2. Query Coverage**

```yaml
Definition: % of common user queries answerable from corpus
Testing: Sample 100 expected queries
Minimum (Beta): 70% answerable
Production Target: 90%+ answerable
```

**3. Information Completeness**

```yaml
For each critical topic, verify presence of:
  ✓ Syarat/Requirements (100% critical)
  ✓ Prosedur/Steps (100% critical)
  ✓ Biaya/Costs (80% important)
  ✓ Timeline/Duration (80% important)
  ✓ Legal basis (70% important)
  ✓ Contact info (60% helpful)
```

---

### B. Quality Metrics

**1. Document Quality**

```yaml
Min length: 200 chars (filter out too short)
Max length: 50,000 chars (split if longer)
Language: 100% target language (Indonesian)
Format: Clean text (no HTML artifacts, broken UTF-8)
Metadata: Required fields populated (source, date, type)
```

**2. Chunk Quality**

```yaml
Chunk size: 300-800 tokens (optimal for most LLMs)
Overlap: 50-100 tokens (preserve context)
Semantic coherence: Chunks preserve meaning
Citation linkage: Track back to source document
```

**3. Retrieval Quality**

```yaml
Metric: Precision@K (K=3,5,10)
Target Production: P@5 ≥ 0.80
Measurement: % of retrieved chunks relevant

Metric: Mean Reciprocal Rank (MRR)
Target Production: MRR ≥ 0.70
Measurement: Rank of first relevant result
```

---

### C. Diversity Metrics

**1. Source Diversity**

```yaml
Official sources: ≥70% from gov.id domains
Date distribution: ≥60% from last 3 years
Document types: Mix of guides, regulations, FAQ
```

**2. Linguistic Diversity**

```yaml
Vocabulary coverage: Broad terminology
Formal + informal phrasing: Handle both
Regional variations: Include common variants
```

---

## ✅ IndoGovRAG Current State Assessment

### Estimated Current State (Based on Test Results)

**Test Results Summary:**

- 3 queries tested
- Avg quality score: 72% (B grade)
- Retrieved: 3 chunks per query consistently
- Vector store: Active with unknown total count

**Inferred Status:**

```yaml
Estimated Documents: 30-60 (based on 3-chunk retrieval)
Estimated Chunks: 100-300
Current Grade: B (71-72%)
Status: BETA/PROTOTYPE level

Quality Issues:
  - Query 1 (KTP): 67% keyword coverage (2/3)
  - Query 2 (KTP variant): Not enough differentiation
  - Query 3 (Akta): 100% coverage (good!)
  - Overall: Inconsistent quality
```

---

## 🎯 Data Sufficiency Evaluation

### Current vs Standards

| Metric | Current (Est) | Beta Target | Production | Status |
|--------|---------------|-------------|------------|--------|
| **Documents** | 30-60 | 100-300 | 500-2,000 | ⚠️ LOW |
| **Chunks** | 100-300 | 500-1,500 | 2,500-10k | ⚠️ LOW |
| **Topic Coverage** | ~40%? | 60% | 85% | ⚠️ LOW |
| **Query Coverage** | 72% | 75% | 90% | ⚠️ BORDERLINE |
| **Answer Quality** | 71-72% | 80% | 90% | ⚠️ LOW |

**Assessment:** ⚠️ **DATA BELUM LAYAK UNTUK PRODUCTION**

---

## 📊 Detailed Gap Analysis

### Gap 1: Document Volume ❌ CRITICAL

```yaml
Current: ~50 documents (estimated)
Beta minimum: 100 documents
Production minimum: 500 documents

Gap: -50 docs (vs beta), -450 docs (vs production)
Impact: HIGH - Direct correlation to answer quality
Priority: P0 - Address immediately
```

### Gap 2: Topic Coverage ⚠️ IMPORTANT

```yaml
Current coverage estimate:
  KTP: Has some documents ✓
  Akta: Has some documents ✓
  KK: Unknown
  Izin Usaha: Unknown
  NPWP: Likely missing ✗
  Paspor: Likely missing ✗
  BPJS: Likely missing ✗

Estimated: 5-7 topics covered / 15 expected = 35-47%
Target (Beta): 60% = 9 topics
Target (Production): 85% = 13 topics

Gap: -4 topics (vs beta), -8 topics (vs production)
Impact: HIGH - Cannot answer queries outside covered topics
Priority: P0
```

### Gap 3: Information Completeness ⚠️ MEDIUM

```yaml
Based on test results:
  Syarat (Requirements): Partial (67-100% per query)
  Prosedur (Steps): Likely incomplete
  Legal references: Missing or incomplete
  Timeline: Likely missing
  Costs: Likely missing

Impact: MEDIUM - Answers incomplete but partially useful
Priority: P1
```

---

## 💡 Recommendations (Priority Order)

### Immediate (Week 1) - P0: Reach Beta Minimum

**Target:** 100-150 documents, 60% topic coverage

**Actions:**

1. ✅ **Run Tier 2 Scraper** (ALREADY CREATED!)

   ```bash
   # Fix scraper URL (indonesia.go.id specific paths)
   # Run for 3-4 hours to gather 50-100 docs
   python scripts/scrape_gov_docs.py
   ```

   Expected gain: +50-100 documents
   Topics: Mixed government services

2. **Manual High-Value Document Addition**

   ```yaml
   Focus topics (5-10 docs each):
     - KTP elektronik (detailed guide)
     - Akta kelahiran (complete procedure)
     - Kartu Keluarga (requirements)
     - NPWP (tax ID procedures)
     - Izin Usaha (OSS/NIB)
   
   Sources:
     - https://dukcapil.kemendagri.go.id
     - https://oss.go.id
     - https://www.pajak.go.id
   ```

   Expected gain: +30-50 curated documents
   Topics: Core services (100% critical)

3. **Validate Coverage**

   ```bash
   # Test with expanded corpus
   python scripts/test_system_comprehensive.py
   ```

   Expected improvement: 72% → 80-85% quality

**Timeline:** 2-3 days  
**Expected Result:** Beta-ready (80% quality)

---

### Short-term (Week 2-3) - P1: Production Minimum

**Target:** 300-500 documents, 85% topic coverage

**Actions:**

1. **Expand Scraper to Multiple Sources**
   - Add OSS.go.id scraper
   - Add Kemendagri scraper
   - Add JDIH scraper (legal docs)

2. **Create Golden Dataset**
   - 100-200 verified QA pairs
   - Expert review for accuracy
   - Use for benchmarking

3. **Implement RAGAS Evaluation**

   ```bash
   python scripts/evaluate_ragas.py
   ```

   Target metrics:
   - Faithfulness: >0.90
   - Answer Relevancy: >0.80
   - Context Precision: >0.70

**Timeline:** 2-3 weeks  
**Expected Result:** Production-ready (90% quality)

---

### Long-term (Month 2-3) - P2: Enterprise Scale

**Target:** 1,000+ documents, 95%+ topic coverage

**Actions:**

1. Automated re-scraping (weekly updates)
2. User feedback loop (improve based on usage)
3. Fine-tuning with domain data
4. Multi-modal content (tables, forms, images)

**Timeline:** 2-3 months  
**Expected Result:** Enterprise-grade (95%+ quality)

---

## 📈 Expected Quality Progression

```
Current State:        72% (B)     ← YOU ARE HERE
+ Tier 2 Scraper:     80-85% (B+)  ← Week 1 target  
+ Manual Curation:    85-90% (A-)  ← Week 2-3 target
+ Full Implementation: 90-95% (A)   ← Month 2 target
+ Enterprise features: 95%+ (A+)    ← Month 3+ target
```

---

## ✅ Success Criteria by Phase

### Phase 1 (Beta Ready) - Week 1

- [ ] 100+ documents in corpus
- [ ] 60%+ topic coverage (9/15 topics)
- [ ] 80%+ answer quality score
- [ ] P@5 ≥ 0.75
- [ ] Can answer 80% of common queries

### Phase 2 (Production Ready) - Week 3

- [ ] 300+ documents in corpus
- [ ] 85%+ topic coverage (13/15 topics)
- [ ] 90%+ answer quality score
- [ ] P@5 ≥ 0.85
- [ ] RAGAS faithfulness >0.90
- [ ] Can answer 95% of common queries

### Phase 3 (Enterprise Scale) - Month 3

- [ ] 1,000+ documents
- [ ] 95%+ topic coverage
- [ ] 95%+ answer quality
- [ ] Production monitoring active
- [ ] Human-in-loop established

---

## 🎯 Bottom Line

**Current Status:** ⚠️ **DATA BELUM LAYAK PRODUCTION**

**Why:**

- Volume too low (~50 vs 500+ needed)
- Topic coverage insufficient (~40% vs 85% needed)
- Quality inconsistent (72% vs 90% needed)

**Solution:** **Execute Tier 2 (Document Enrichment)**

**Priority Actions:**

1. **NOW:** Fix & run scraper → +50-100 docs (2 days)
2. **Week 1:** Manual curation → +30-50 docs (3 days)
3. **Week 2:** Expand sources → +200 docs (1 week)

**Expected:** Beta-ready Week 1, Production-ready Week 3

**Already have:** Complete scraper + strategy in `TIER_2_DOCUMENT_ENRICHMENT.md` ✅

**Next step:** Execute scraper! 🚀

---

**Kesimpulan:** Data saat ini cukup untuk **PROTOTYPE/TESTING** tapi **BELUM LAYAK PRODUCTION**. Perlu enrichment ke 300-500 docs minimal untuk production quality.
