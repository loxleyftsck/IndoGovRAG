# ⚡ Quick Action Plan - Critical Items

**Date:** 11 Januari 2026, 21:52  
**Status:** Resolving 2 critical warnings from audit

---

## 🎯 Critical Item #1: Unit Test Failure

**Test:** `test_chunk_metadata`  
**Status:** 🔧 INVESTIGATING  
**Priority:** HIGH (for 100% pass rate)

**Action:**

1. ✅ Run isolated test to see exact error
2. 🔄 Analyze failure cause
3. 🔄 Apply fix
4. 🔄 Verify all tests pass

**Target:** 23/23 tests passing (100%)

---

## 🎯 Critical Item #2: Legal Documents (0 docs)

**Current:** 0 legal foundation documents  
**Target:** 10-15 UU/PP/Perpres  
**Priority:** MEDIUM (non-blocking for beta)

**Immediate Action Plan:**

### Option A: Manual Download (RECOMMENDED - 2-3 hours)

**Top 5 Priority Legal Docs:**

1. **UU 24/2013** - Administrasi Kependudukan (KTP/KK/Akta)
2. **UU 23/2006** - Administrasi Kependudukan (Akta)  
3. **UU 28/2007** - Ketentuan Umum dan Tata Cara Perpajakan (NPWP)
4. **PP 5/2021** - Penyelenggaraan Perizinan Berusaha
5. **Perpres 96/2018** - Persyaratan dan Tata Cara NIB

**Steps:**

```bash
1. Go to: https://jdih.setkab.go.id
2. Search each UU individually
3. Download PDF
4. Convert to text:
   python scripts/convert_pdf_to_text.py <file.pdf>
5. Tag as legal:
   python scripts/tag_legal_doc.py <file.txt> --type uu
6. Ingest to vector DB:
   python scripts/ingest_legal_docs.py
```

**Expected Impact:**

- +10-15 legal documents
- +20% corpus size
- +30-40% legal query accuracy

### Option B: ScrapingBee API (AUTOMATED - 30 min)

**For remaining failed URLs:**

```python
# Use ScrapingBee for anti-scraping sites
import requests

urls = [
    "https://disdukcapil.jakarta.go.id/...",  # SIM/STNK
    "https://jdih.setkab.go.id/...",          # Legal docs
]

api_key = "YOUR_SCRAPINGBEE_KEY"  # Free tier: 1000 pages

for url in urls:
    response = requests.get(
        "https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": api_key,
            "url": url,
            "render_js": "true"
        }
    )
    # Process response...
```

**Cost:** FREE (1000 pages/month)

---

## 📊 Progress Tracker

### Before

- ✅ E2E Tests: 4/4 (100%)
- ⚠️ Unit Tests: 22/23 (95.7%)
- ⚠️ Legal Docs: 0
- ⚠️ Total Docs: 47 (scraped only)

### Target (This Session)

- ✅ E2E Tests: 4/4 (100%)
- 🎯 Unit Tests: 23/23 (100%)
- 📋 Legal Docs: Document strategy ✅
- ✅ Total Docs: 47 categorized

### After (Next Session)

- ✅ Unit Tests: 23/23 (100%)
- ✅ Legal Docs: 10-15
- ✅ Total Docs: 110-120

---

## ⏱️ Time Estimates

**This Session (Now):**

- Test fix: 15-30 minutes
- Legal strategy doc: ✅ DONE

**Next Session (Optional):**

- Manual legal doc download: 2-3 hours
- Or ScrapingBee setup: 30 minutes

---

## 🎯 Immediate Actions (Next 30 min)

1. ✅ Audit complete
2. 🔄 Fix unit test (in progress)
3. ✅ Document legal docs strategy
4. 🔄 Verify 100% test pass
5. ✅ Update final artifacts

**After this:** System will be 100% tested with clear roadmap for legal docs!
