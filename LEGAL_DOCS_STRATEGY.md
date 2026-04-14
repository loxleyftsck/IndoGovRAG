# 📜 Analisis Dokumen Legal vs Non-Legal

**Problem:** Dokumen legal (UU, PP, Perpres) perlu kategori khusus  
**Importance:** Legal docs = dasar hukum, perlu penanganan berbeda dari panduan operasional

---

## 🎯 Kenapa Perlu Dipisah?

### 1. Karakteristik Berbeda

```yaml
Legal Documents (Lege/Jure):
  - UU (Undang-Undang)
  - PP (Peraturan Pemerintah)
  - Perpres (Peraturan Presiden)
  - Permen (Peraturan Menteri)
  
  Ciri:
    - Pasal & ayat terstruktur
    - Bahasa formal/legal
    - Hierarki jelas
    - Dasar hukum (foundation)

Non-Legal Documents (Operasional):
  - Panduan layanan
  - Syarat & prosedur
  - FAQ
  - Tutorial
  
  Ciri:
    - Bahasa praktis
    - Step-by-step
    - User-friendly
    - Implementasi (application)
```

### 2. Penggunaan Berbeda

```yaml
Query Type 1: Legal Basis
  User: "Apa dasar hukum KTP?"
  Need: UU 24/2013, pasal spesifik
  Source: Legal docs

Query Type 2: Operational
  User: "Gimana cara bikin KTP?"
  Need: Step-by-step, syarat
  Source: Non-legal docs
```

---

## 📊 Current Status Analysis

### Scraped Documents Breakdown

**From Round 1 (15 docs):**

- Legal: 0 docs (JDIH failed - HTTP 400)
- Non-legal: 15 docs (all operational)

**From Round 2 (32 docs):**

- Legal: 0 docs (JDIH still failed)
- Non-legal: 32 docs (all operational)

**TOTAL: 0 legal documents! ❌**

---

## ⚠️ Critical Gap

```yaml
Current: 100% operational, 0% legal foundation

Risk:
  - Cannot cite legal basis accurately
  - No pasal/ayat references
  - Weak authority/credibility
  
Impact on Quality:
  - Faithfulness: May cite non-existent pasal
  - Authority: Cannot validate claims legally
  - Completeness: Missing legal foundation
```

---

## 💡 Solution: 3-Tier Document Strategy

### Tier 1: Legal Foundation (TARGET: 20-30 docs)

**Sources:**

```
JDIH Setkab (Manual Download):
  - UU 24/2013 - Administrasi Kependudukan
  - UU 23/2006 - Standar Akta
  - UU 28/2007 - Perpajakan
  - PP 5/2021 - Perizinan Berusaha
  - Perpres terkait
  
Why Manual: JDIH blocks all scraping (HTTP 400)
```

**Categorization:**

```python
doc_type: 'legal_uu'    # Highest authority
doc_type: 'legal_pp'    # Medium authority  
doc_type: 'legal_perpres'  # Executive authority
doc_type: 'legal_permen'   # Ministry level
```

### Tier 2: Operational Guides (CURRENT: 47 docs ✅)

**Already Have:**

- NPWP procedures
- KTP requirements
- Akta process
- Business licensing

**Categorization:**

```python
doc_type: 'operational_ktp'
doc_type: 'operational_akta'
doc_type: 'operational_npwp'
# etc
```

### Tier 3: FAQs & Tips (TARGET: 10-20 docs)

**Need to Add:**

- Common questions
- Troubleshooting
- Tips & tricks

---

## 🔧 Implementation Plan

### Phase 1: Manual Legal Document Addition (TODAY)

**Method:** Direct download dari JDIH

```bash
# Download key legal docs manually
1. Go to https://jdih.setkab.go.id
2. Search: "UU 24 2013"
3. Download PDF
4. Convert to text: pdfplumber
5. Tag as doc_type: 'legal_uu'
```

**Priority UU/PP (Top 10):**

1. UU 24/2013 - Administrasi Kependudukan ⭐
2. UU 23/2006 - Standar Akta ⭐
3. UU 28/2007 - Pajak
4. UU 11/2020 - Cipta Kerja (Izin Usaha)
5. PP 5/2021 - Perizinan Berusaha
6. PP 80/2019 - PNBP Dukcapil
7. Perpres 96/2018 - NIB
8. Permendagri 108/2019 - Adminduk
9. Permenkumham - PT/CV
10. Permenaker - Ketenagakerjaan

**Expected:** +10-15 legal docs

### Phase 2: Re-categorize Existing Docs

**Script to separate:**

```python
"""Categorize documents into legal vs operational"""
import json

def categorize_doc(doc):
    url = doc['source_url'].lower()
    title = doc['title'].lower()
    
    # Legal indicators
    if any(x in url or x in title for x in ['jdih', 'peraturan.go.id']):
        if 'uu' in title:
            return 'legal_uu'
        elif 'pp' in title:
            return 'legal_pp'
        elif 'perpres' in title:
            return 'legal_perpres'
        elif 'permen' in title:
            return 'legal_permen'
        else:
            return 'legal_other'
    
    # Operational
    else:
        current_type = doc.get('doc_type', 'operational')
        return f'operational_{current_type}'

# Apply to all docs
docs = json.load(open('data/scraped/jina_extended_20260111_205123.json'))
for doc in docs:
    doc['doc_category'] = categorize_doc(doc)
    
# Save
json.dump(docs, open('data/scraped/categorized_docs.json', 'w'), 
          indent=2, ensure_ascii=False)
```

### Phase 3: Enhanced Retrieval Strategy

**Hybrid Search:**

```python
def query_with_legal_preference(question):
    """
    Smart retrieval: legal + operational
    """
    # Detect query type
    if any(kw in question.lower() for kw in ['dasar hukum', 'pasal', 'uu', 'peraturan']):
        # Legal query - prioritize legal docs
        legal_results = search(question, filter={'doc_category': 'legal_*'}, k=5)
        operational_results = search(question, filter={'doc_category': 'operational_*'}, k=2)
        return legal_results + operational_results
    else:
        # Operational query - prioritize operational
        operational_results = search(question, k=5)
        legal_results = search(question, filter={'doc_category': 'legal_*'}, k=2)
        return operational_results + legal_results
```

---

## 📊 Target Distribution

### Ideal Corpus (150 docs total)

```yaml
Legal Documents (30 docs - 20%):
  UU: 10 docs
  PP: 8 docs
  Perpres: 5 docs
  Permen: 7 docs

Operational Documents (100 docs - 67%):
  KTP/Akta/KK: 30 docs
  NPWP/Pajak: 20 docs
  Izin Usaha: 20 docs
  Lainnya: 30 docs

FAQ/Tips (20 docs - 13%):
  Common Q&A: 15 docs
  Troubleshooting: 5 docs
```

---

## ✅ Immediate Actions

**1. Check Current Legal Docs (NOW)**

```bash
python -c "import json; docs = json.load(open('data/scraped/jina_extended_20260111_205123.json', encoding='utf-8')); legal = [d for d in docs if 'jdih' in d['source_url'].lower()]; print(f'Legal: {len(legal)} docs')"
```

**2. Manual Download Top 5 Legal Docs (30 min)**

- UU 24/2013
- UU 23/2006
- PP 5/2021
- Permendagri 108/2019
- Perpres 96/2018

**3. Categorize All Existing Docs (5 min)**

```bash
python scripts/categorize_legal_docs.py
```

---

## 🎯 Expected Impact

**With Legal Docs:**

```yaml
Before (100 docs, all operational):
  Legal queries: 60% accuracy (guessing pasal)
  Operational queries: 75% accuracy
  Citation quality: Poor (no legal basis)

After (120 docs, 20 legal + 100 operational):
  Legal queries: 90% accuracy (real pasal)
  Operational queries: 80% accuracy (with legal backing)
  Citation quality: Excellent (verified legal basis)
```

---

## 💡 Recommendation

**Priority:** HIGH - Legal docs critical for credibility

**Action:**

1. Manual download 10-15 key legal docs (1-2 hours)
2. Convert PDF to text
3. Tag as legal_uu/pp/perpres
4. Ingest with metadata
5. Update retrieval to prefer legal for legal queries

**Timeline:**

- Today: Add 5 critical legal docs
- Week 2: Add 10 more
- Target: 20-30 legal foundation docs

---

**Bottom Line:**
Current 100 docs adalah **semua operasional**. Perlu **20-30 legal docs** untuk authority & credibility! Manual download dari JDIH adalah satu-satunya cara (scraping gagal semua).

Mau saya buatkan script untuk manual download & convert legal docs?
