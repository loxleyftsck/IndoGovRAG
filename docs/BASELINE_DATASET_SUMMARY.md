# 📝 Baseline Test Dataset - Complete

**Week 0 Task:** Create 10 validation questions for Indonesian gov docs
**Status:** ✅ COMPLETE
**Time:** ~1.5 hours

---

## 🎯 What Was Created

### 1. **Baseline Evaluation Dataset**
**File:** [baseline_eval_dataset.json](file:///c:/Users/LENOVO/.gemini/antigravity/playground/magnetic-helix/data/baseline_eval_dataset.json)

**10 Questions covering:**
- ✅ 4x Factual Lookup (easy-medium)
- ✅ 3x Multi-hop Reasoning (medium-hard)
- ✅ 2x Summarization (medium)
- ✅ 1x Edge Case (hard)

### 2. **Question Topics**

| ID | Category | Topic | Difficulty |
|----|----------|-------|------------|
| Q001 | Factual | KTP elektronik requirements | Easy |
| Q002 | Factual | SIM C validity period | Easy |
| Q003 | Factual | OSS vs conventional license | Medium |
| Q004 | Factual | BLT eligibility criteria | Medium |
| Q005 | Reasoning | Home culinary business permits | Medium |
| Q006 | Reasoning | Foreign marriage & residency | Hard |
| Q007 | Reasoning | Lost birth certificate process | Hard |
| Q008 | Summarization | CPNS registration procedure | Medium |
| Q009 | Summarization | Citizen rights & obligations | Medium |
| Q010 | Edge Case | Overseas birth citizenship status | Hard |

### 3. **Validation Tools**

**Script:** [validate_dataset.py](file:///c:/Users/LENOVO/.gemini/antigravity/playground/magnetic-helix/validate_dataset.py)

**Features:**
- ✅ Structure validation
- ✅ Required field checking
- ✅ Category distribution analysis
- ✅ Keyword consistency check
- ✅ Question preview generator
- ✅ Export to plain text

**Exported:** [questions_only.txt](file:///c:/Users/LENOVO/.gemini/antigravity/playground/magnetic-helix/data/questions_only.txt)

---

## 📊 Dataset Validation Results

```
✅ Dataset is VALID!

📊 Statistics:
   Total Questions: 10
   
   Categories:
      - factual_lookup: 4
      - multi_hop_reasoning: 3
      - summarization: 2
      - edge_case: 1
   
   Difficulties:
      - easy: 2
      - medium: 5
      - hard: 3
```

---

## 📋 Sample Questions

### Q001 - Factual Lookup (Easy)
**Question:** Apa saja persyaratan dokumen untuk mengajukan KTP elektronik?

**Ground Truth:** Persyaratan dokumen untuk KTP elektronik meliputi: (1) Kartu Keluarga asli dan fotokopi, (2) Akta kelahiran atau surat kenal lahir, (3) Surat keterangan pindah bagi penduduk yang pindah dalam wilayah NKRI, (4) Pas foto berwarna ukuran 3x4 sebanyak 2 lembar, (5) Surat keterangan perekaman KTP-el dari daerah asal bagi penduduk yang pindah.

**Keywords:** Kartu Keluarga, Akta kelahiran, pas foto

---

### Q005 - Multi-hop Reasoning (Medium)
**Question:** Jika seseorang ingin membuka usaha kuliner di rumah, izin apa saja yang diperlukan dan bagaimana prosesnya?

**Ground Truth:** Untuk usaha kuliner rumahan diperlukan: (1) NIB (Nomor Induk Berusaha) melalui OSS untuk legalitas usaha, (2) Sertifikat halal dari MUI/BPJPH jika menjual produk halal, (3) Izin PIRT (Pangan Industri Rumah Tangga) dari Dinas Kesehatan setempat, (4) Sertifikat laik higiene dan sanitasi. Prosesnya: Pertama daftar NIB di OSS online, kemudian mengajukan PIRT dengan membawa sampel produk dan mengikuti penyuluhan keamanan pangan, lalu mengurus sertifikat halal secara paralel, dan terakhir mengikuti inspeksi sanitasi dari Dinkes.

**Keywords:** NIB, PIRT, Dinkes, proses

---

### Q010 - Edge Case (Hard)
**Question:** Bagaimana status kewarganegaraan anak yang lahir di luar negeri dari orang tua WNI yang sudah tidak memiliki paspor Indonesia?

**Ground Truth:** Menurut UU Kewarganegaraan, anak yang lahir dari orang tua WNI tetap berhak atas kewarganegaraan Indonesia berdasarkan asas ius sanguinis (hak darah), meskipun orang tua tidak memiliki paspor Indonesia yang masih berlaku. Namun, untuk mengurus dokumen kewarganegaraan anak, orang tua perlu: (1) Melaporkan kelahiran ke KBRI/Konsulat terdekat maksimal 1 tahun setelah kelahiran, (2) Membuktikan kewarganegaraan Indonesia orang tua meskipun paspor habis masa berlaku (dengan menunjukkan paspor lama, KTP, atau dokumen kewarganegaraan lain), (3) Mengajukan permohonan penetapan kewarganegaraan anak di KBRI/Konsulat, (4) Anak akan mendapatkan Surat Keterangan Kewarganegaraan RI dan dapat dibuatkan paspor Indonesia. Penting: Jika tidak dilaporkan sampai anak berusia 18 tahun, anak harus memilih kewarganegaraan dan mengajukan permohonan menjadi WNI.

**Keywords:** ius sanguinis, KBRI, 18 tahun, melaporkan

---

## ✅ Quality Checklist

- [x] **Diverse question types** - Factual, reasoning, summarization, edge cases
- [x] **Covers common use cases** - KTP, SIM, CPNS, business licenses
- [x] **Includes edge cases** - Ambiguous citizenship scenario
- [x] **Natural Indonesian language** - All questions in natural Bahasa
- [x] **Realistic scenarios** - Based on actual gov regulations
- [x] **Detailed ground truth** - Comprehensive answers with sources
- [x] **Evaluation criteria** - Clear rubrics for each question
- [x] **Peer review ready** - JSON structure allows easy review

---

## 🔧 Dataset Structure

```json
{
  "metadata": {
    "version": "1.0",
    "created_date": "2024-12-17",
    "total_questions": 10,
    "categories": {...}
  },
  "questions": [
    {
      "id": "Q001",
      "category": "factual_lookup",
      "difficulty": "easy",
      "question": "...",
      "question_en": "...",
      "ground_truth": "...",
      "keywords_must_have": [...],
      "evaluation_criteria": {...}
    }
  ],
  "validation_notes": {...}
}
```

---

## 📈 Usage in RAG System

### Testing RAG Responses

```python
import json

# Load baseline dataset
with open('data/baseline_eval_dataset.json', 'r') as f:
    dataset = json.load(f)

# Test each question
for q in dataset['questions']:
    # Query RAG system
    response = rag_system.query(q['question'])
    
    # Compare with ground truth
    score = evaluate_response(
        response=response,
        ground_truth=q['ground_truth'],
        keywords=q['keywords_must_have']
    )
    
    print(f"{q['id']}: {score}")
```

### Evaluation Criteria

Each question includes:
- **keywords_must_have**: Required keywords in response
- **evaluation_criteria**: Rubric with factual_accuracy, completeness, language_quality
- **expected_answer_length**: short/medium/long for response validation

---

## 🚀 Next Steps (Week 2)

1. **Peer Review** (pending)
   - Review ground truth accuracy
   - Validate question clarity
   - Add reviewer notes to JSON

2. **Expand to 100 Questions** (Week 2)
   - 30 factual lookup
   - 25 multi-hop reasoning
   - 25 summarization
   - 20 edge cases

3. **Integrate with RAGAS** (Week 2)
   - Use as test dataset for automated evaluation
   - Generate synthetic variations
   - Track baseline vs optimized performance

---

## ✅ Week 0 Progress Update

**Completed:**
- [x] Gemini quota tracker (2h)
- [x] Baseline test dataset (1.5h)

**Remaining:**
- [ ] Indonesian NLP Benchmarking (3h)
- [ ] Data source audit (3h)
- [ ] Experiment tracking setup (2h)
- [ ] Data quality checklist (1h)
- [ ] LLM fallback testing (2h)

**Total Progress:** 2/7 tasks (29%)

---

**Created:** 2024-12-17  
**Files:**
- `data/baseline_eval_dataset.json` (10 questions)
- `validate_dataset.py` (validator script)
- `data/questions_only.txt` (quick reference)

**Status:** ✅ READY FOR WEEK 1 TESTING
