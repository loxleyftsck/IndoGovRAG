# 🔥 PHASE 1 QUICK START - HARI INI!

**Goal:** 3 chunks → 50+ chunks  
**Time:** 30-60 menit  
**Method:** Manual download

---

## 📥 STEP-BY-STEP DOWNLOAD

### **1. JDIH Setkab (Prioritas!)**

**Website:** https://jdih.setkab.go.id

**Dokumen Priority:**

#### **A. Administrasi Kependudukan (KTP):**
1. Search: "UU 24 Tahun 2013" (KTP Elektronik)
2. Search: "UU 23 Tahun 2006" (Adminduk)
3. Download PDF → save ke `data/raw/phase1/uu24_2013_ktp.pdf`

#### **B. Perpajakan (NPWP):**
1. Search: "UU 28 Tahun 2007" (Perpajakan)
2. Search: "Perpres NPWP"
3. Download → save ke `data/raw/phase1/`

#### **C. Jaminan Sosial (BPJS):**
1. Search: "UU 24 Tahun 2011" (BPJS)
2. Search: "Perpres 12 Tahun 2013" (JKN)
3. Download → save ke `data/raw/phase1/`

#### **D. Keimigrasian (Paspor):**
1. Search: "UU 6 Tahun 2011" (Keimigrasian)
2. Download → save ke `data/raw/phase1/`

#### **E. Lalu Lintas (SIM):**
1. Search: "UU 22 Tahun 2009" (Lalu Lintas)
2. Download → save ke `data/raw/phase1/`

---

### **2. Peraturan.go.id (Alternatif)**

**Website:** https://peraturan.go.id

**Jika JDIH lambat/susah:**
- Same searches
- Usually has better download speed
- More complete metadata

---

## ⚡ LOAD KE DATABASE

**After download 10 PDFs:**

```bash
# Method 1: Using existing script
python scripts/load_sample_docs.py

# Method 2: Manual (if script error)
python -c "
import sys
sys.path.insert(0, '.')
from src.data.pdf_loader import PDFLoader
from src.retrieval.vector_search import VectorStore

loader = PDFLoader()
vs = VectorStore()

# Load PDFs
docs = loader.load_directory('data/raw/phase1')
print(f'Loaded {len(docs)} documents')

# Add to database
for doc in docs:
    chunks = loader.chunk_document(doc)
    for chunk in chunks:
        vs.add_document(chunk)
        
print(f'Total chunks now: {vs.collection.count()}')
"
```

---

## ✅ VERIFY

**Test query:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Persyaratan membuat KTP elektronik"}'
```

**Expected:**
- Confidence: >60%
- Sources: 1-3 documents
- Answer: Real legal requirements

---

## 📊 PROGRESS CHECKLIST

- [ ] Downloaded 5+ PDFs from JDIH
- [ ] Saved to data/raw/phase1/
- [ ] Ran load script
- [ ] Verified count >50 chunks
- [ ] Tested query (confidence >60%)

---

## 🎯 TARGET DOCUMENTS

**Minimum 10 PDFs:**

1. ✅ UU 24/2013 (KTP)
2. ✅ UU 23/2006 (Adminduk)
3. ✅ UU 28/2007 (Pajak)
4. ✅ UU 24/2011 (BPJS)
5. ✅ UU 6/2011 (Paspor)
6. ✅ UU 22/2009 (SIM)
7. ⬜ PP tentang Pendaftaran Penduduk
8. ⬜ Perpres NPWP
9. ⬜ Permen terkait
10. ⬜ Free choice (any legal doc)

---

## 🚨 TROUBLESHOOTING

**Q: Website JDIH lambat?**
A: Use peraturan.go.id instead

**Q: Script error "ModuleNotFoundError"?**
A: Use Method 2 (manual Python code above)

**Q: PDF tidak ter-load?**
A: Check file tidak corrupt, format benar (.pdf)

---

**START NOW!** 30 menit = working system! 🔥
