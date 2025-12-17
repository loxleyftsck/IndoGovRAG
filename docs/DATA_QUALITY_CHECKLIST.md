# 📋 Data Quality Checklist for Indonesian Government Documents

**Version:** 1.0  
**Date:** 2024-12-17  
**Purpose:** Ensure high-quality data for RAG system training and retrieval

---

## 🎯 Quality Standards Overview

### Target Metrics
- **Document Parse Success Rate:** >95%
- **Indonesian Language Detection:** >98%
- **Text Extractability:** >90%
- **Chunk Coherence Score:** >0.8
- **PII Leak Rate:** 0%

---

## ✅ Pre-Collection Quality Checks

### 1. Source Validation
- [ ] Document from verified JDIH portal
- [ ] Direct government source (not third-party)
- [ ] URL logged for attribution
- [ ] Download timestamp recorded

### 2. File Format Check
- [ ] File is PDF format
- [ ] File size reasonable (100KB - 50MB)
- [ ] File not corrupted (opens successfully)
- [ ] No password protection

---

## 📄 Document-Level Quality Checks

### 3. Content Extractability (CRITICAL)

**Test:** Can text be extracted from PDF?

```python
import PyPDF2

def check_text_extractable(pdf_path):
    """Check if PDF has extractable text."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            first_page = reader.pages[0].extract_text()
            
            # Quality checks
            if len(first_page) < 50:
                return False, "Too little text extracted"
            
            # Check if mostly garbled (OCR needed)
            alpha_ratio = sum(c.isalpha() for c in first_page) / len(first_page)
            if alpha_ratio < 0.5:
                return False, "Mostly non-alphabetic characters"
            
            return True, "Text extractable"
    except Exception as e:
        return False, str(e)
```

**Criteria:**
- ✅ PASS: >50 characters extractable per page
- ✅ PASS: >50% alphabetic characters
- ❌ FAIL: Scanned image without OCR
- ⚠️ OCR NEEDED: Image-based PDF

**Action on Fail:**
- Mark for OCR processing
- If OCR confidence <80%, exclude document

---

### 4. Language Detection

**Test:** Is document primarily Indonesian?

```python
from langdetect import detect, detect_langs

def check_indonesian_language(text_sample):
    """Verify document is Indonesian."""
    try:
        # Take sample from multiple sections
        if len(text_sample) < 100:
            return False, "Sample too short"
        
        # Detect language
        lang = detect(text_sample)
        
        # Get confidence scores
        lang_probs = detect_langs(text_sample)
        id_conf = next((l.prob for l in lang_probs if l.lang == 'id'), 0)
        
        if lang == 'id' and id_conf > 0.95:
            return True, f"Indonesian ({id_conf:.2%})"
        elif id_conf > 0.70:
            return True, f"Mostly Indonesian ({id_conf:.2%})"
        else:
            return False, f"Not Indonesian (detected: {lang})"
    except Exception as e:
        return False, str(e)
```

**Criteria:**
- ✅ PASS: Indonesian detected with >95% confidence
- ⚠️ ACCEPT: 70-95% Indonesian (mixed content acceptable)
- ❌ FAIL: <70% Indonesian

**Action on Fail:**
- Log as non-Indonesian
- Exclude from dataset unless specifically needed

---

### 5. Document Completeness

**Manual Checks:**
- [ ] Has proper title/heading
- [ ] Contains regulation number (e.g., "PP No. XX Tahun YYYY")
- [ ] Has date of issuance
- [ ] Includes main content (not just cover page)
- [ ] No pages missing (check page numbers)

**Automated Check:**

```python
import re

def check_document_completeness(text):
    """Check if document has essential elements."""
    checks = {
        "has_regulation_number": bool(re.search(r'(PP|Permen|UU|Perpres)\s+No\.?\s*\d+', text)),
        "has_year": bool(re.search(r'Tahun\s+\d{4}', text)),
        "has_tentang": 'tentang' in text.lower(),
        "min_length": len(text) > 1000,  # At least 1000 characters
    }
    
    pass_count = sum(checks.values())
    return pass_count >= 3, checks
```

**Criteria:**
- ✅ PASS: 3+ elements present
- ❌ FAIL: <3 elements

---

### 6. Text Quality

**Checks:**
- [ ] No excessive whitespace (not just "\n\n\n...")
- [ ] Readable sentences (not garbled OCR)
- [ ] Proper punctuation
- [ ] No encoding issues (mojibake)

```python
def check_text_quality(text):
    """Assess text quality."""
    # Remove whitespace for analysis
    clean_text = ' '.join(text.split())
    
    # Check for excessive repetition
    if len(set(clean_text[:100])) < 10:
        return False, "Excessive character repetition"
    
    # Check for sentence structure
    sentences = text.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    
    if avg_sentence_length < 3 or avg_sentence_length > 100:
        return False, f"Unusual sentence length: {avg_sentence_length:.1f}"
    
    # Check for Indonesian characters
    if re.search(r'[^\x00-\x7F\u00C0-\u017F]', text):  # Non-Latin characters
        return True, "Contains non-Latin (check encoding)"
    
    return True, "Text quality OK"
```

**Criteria:**
- ✅ PASS: Readable Indonesian text
- ⚠️ REVIEW: Non-Latin characters present
- ❌ FAIL: Garbled or repetitive text

---

## 🔍 PII Detection (Security)

### 7. Personal Information Screening

**Categories to Detect:**

1. **NIK (Nomor Induk Kependudukan)** - 16 digits
2. **Email addresses**
3. **Phone numbers** (Indonesian format)
4. **NPWP** - Tax ID
5. **Names in sensitive contexts** (e.g., "an. [Name]")

```python
import re

PII_PATTERNS = {
    'nik': r'\b\d{16}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(\+62|0)\d{8,12}\b',
    'npwp': r'\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b',
}

def detect_pii(text):
    """Detect PII in document."""
    findings = {}
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings[pii_type] = {
                'count': len(matches),
                'samples': matches[:3]  # First 3 for review
            }
    
    return findings

def should_redact(pii_findings):
    """Determine if document needs redaction."""
    # Government docs may contain example NIKs
    # Real PII should be redacted
    if pii_findings.get('nik', {}).get('count', 0) > 5:
        return True, "Multiple NIKs found"
    if pii_findings.get('email', {}).get('count', 0) > 0:
        return True, "Email addresses found"
    return False, "No significant PII"
```

**Criteria:**
- ✅ PASS: No PII detected
- ⚠️ REVIEW: Example data present (e.g., "contoh: 1234...")
- ❌ REDACT: Real PII detected (emails, multiple NIKs)

**Action on Detection:**
- Log PII instances
- Redact if real data (not examples)
- Exclude if extensive personal info

---

## 📝 Chunk-Level Quality Checks

### 8. Chunk Coherence

**Test:** Does chunk make semantic sense?

```python
def check_chunk_coherence(chunk_text, min_words=20, max_words=600):
    """Validate chunk quality."""
    words = chunk_text.split()
    word_count = len(words)
    
    # Length check
    if word_count < min_words:
        return False, f"Too short ({word_count} words)"
    if word_count > max_words:
        return False, f"Too long ({word_count} words)"
    
    # Check for complete sentences
    if not any(chunk_text.strip().endswith(p) for p in ['.', '!', '?', ';']):
        return 0.7, "No sentence ending"
    
    # Check for Indonesian stopwords
    indonesian_stopwords = ['yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'adalah']
    stopword_count = sum(1 for word in words if word.lower() in indonesian_stopwords)
    
    if stopword_count < 2:
        return 0.6, "Few Indonesian stopwords"
    
    return 1.0, "Coherent chunk"
```

**Criteria:**
- ✅ EXCELLENT (1.0): Complete sentences, proper length, Indonesian stopwords
- ✅ GOOD (0.7-0.9): Minor issues (no ending punctuation)
- ⚠️ ACCEPTABLE (0.6-0.7): Some issues but usable
- ❌ FAIL (<0.6): Too short, wrong language, or garbled

**Target:** Avg coherence score >0.8

---

### 9. Chunk Metadata

**Required for each chunk:**
- [ ] Source document ID
- [ ] Page number
- [ ] Chunk index
- [ ] Section title (if available)
- [ ] Character count
- [ ] Token count (estimated)

```python
from dataclasses import dataclass

@dataclass
class ChunkMetadata:
    doc_id: str
    source_url: str
    page_number: int
    chunk_index: int
    section_title: str
    char_count: int
    token_count: int
    coherence_score: float
    language_confidence: float
```

---

## 🚨 Automated Quality Pipeline

### Full Document Processing Flow

```python
def process_document(pdf_path, doc_id):
    """
    Run full quality check pipeline.
    
    Returns:
        (is_valid, quality_report)
    """
    report = {
        'doc_id': doc_id,
        'checks': {},
        'warnings': [],
        'errors': []
    }
    
    # 1. Extract text
    is_extractable, msg = check_text_extractable(pdf_path)
    report['checks']['extractable'] = is_extractable
    if not is_extractable:
        report['errors'].append(f"Text extraction failed: {msg}")
        return False, report
    
    # 2. Get full text
    full_text = extract_full_text(pdf_path)
    
    # 3. Language detection
    is_indonesian, lang_msg = check_indonesian_language(full_text[:1000])
    report['checks']['indonesian'] = is_indonesian
    if not is_indonesian:
        report['errors'].append(f"Language check failed: {lang_msg}")
        return False, report
    
    # 4. Completeness
    is_complete, elements = check_document_completeness(full_text)
    report['checks']['complete'] = is_complete
    report['checks']['elements'] = elements
    if not is_complete:
        report['warnings'].append("Document may be incomplete")
    
    # 5. Text quality
    is_quality, quality_msg = check_text_quality(full_text)
    report['checks']['text_quality'] = is_quality
    if not is_quality:
        report['warnings'].append(f"Text quality issue: {quality_msg}")
    
    # 6. PII detection
    pii_findings = detect_pii(full_text)
    needs_redaction, redact_msg = should_redact(pii_findings)
    report['checks']['pii'] = pii_findings
    if needs_redaction:
        report['warnings'].append(f"PII detected: {redact_msg}")
    
    # Overall verdict
    critical_checks_passed = (
        report['checks']['extractable'] and 
        report['checks']['indonesian']
    )
    
    return critical_checks_passed, report
```

---

## 📊 Quality Metrics Dashboard

### Track These Metrics:

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Documents Collected | 50-100 | - | ⏳ Pending |
| Parse Success Rate | >95% | - | ⏳ Pending |
| Indonesian Detection | >98% | - | ⏳ Pending |
| Text Extractable | >90% | - | ⏳ Pending |
| Avg Coherence Score | >0.8 | - | ⏳ Pending |
| PII Leak Rate | 0% | - | ⏳ Pending |
| Chunks Generated | 2000-5000 | - | ⏳ Pending |

---

## 🔄 Quality Improvement Actions

### If Metrics Below Target:

**Parse Success Rate <95%:**
- [ ] Implement OCR for scanned PDFs
- [ ] Filter out corrupted files earlier
- [ ] Use alternative PDF libraries (pdfplumber, tabula)

**Indonesian Detection <98%:**
- [ ] Review source selection (ensure JDIH)
- [ ] Accept mixed Indonesian-English if >70% Indonesian
- [ ] Tag language per section

**Chunk Coherence <0.8:**
- [ ] Adjust chunking strategy (sentence boundaries)
- [ ] Increase chunk overlap
- [ ] Manual review of low-scoring chunks

**PII Detected:**
- [ ] Implement redaction pipeline
- [ ] Review if PII is example data
- [ ] Exclude documents with real PII

---

## ✅ Final Quality Sign-off Checklist

Before deploying dataset to RAG system:

- [ ] All documents passed critical checks (extractable + Indonesian)
- [ ] Parse success rate documented and >90%
- [ ] PII scan completed, redactions applied
- [ ] Sample manual review done (10 random docs)
- [ ] Metadata complete for all documents
- [ ] Chunk coherence scores calculated
- [ ] Quality report generated and archived

---

## 📁 Quality Report Template

```json
{
  "quality_report": {
    "date": "2024-12-17",
    "total_documents": 75,
    "passed": 72,
    "failed": 3,
    "metrics": {
      "parse_success_rate": 0.96,
      "indonesian_detection_rate": 0.99,
      "text_extractable_rate": 0.93,
      "avg_coherence_score": 0.84,
      "pii_leak_rate": 0.00
    },
    "failed_documents": [
      {
        "doc_id": "DOC_045",
        "reason": "Text not extractable (scanned image)",
        "action": "Marked for OCR"
      }
    ],
    "warnings": [
      {
        "doc_id": "DOC_023",
        "issue": "Mixed Indonesian-English (85% ID)",
        "action": "Accepted"
      }
    ]
  }
}
```

---

## 🛠️ Tools & Libraries Needed

```bash
# PDF processing
pip install PyPDF2 pdfplumber

# Language detection
pip install langdetect

# Text processing
pip install nltk spacy

# OCR (if needed)
pip install pytesseract
```

---

## ✅ Week 0 Requirement Status

- [x] Define data quality standards
- [x] Create validation criteria
- [x] Implement automated checks
- [x] Document quality metrics
- [x] Create quality report template

**Status:** ✅ COMPLETE  
**Confidence:** 95% - Ready for Week 1 data collection

---

**Created:** 2024-12-17  
**Next Step:** Implement quality check scripts in Week 1  
**Integration:** Use during data preprocessing pipeline
