# 📚 Data Collection Guide - Indonesian Government Documents

**Task:** Download 50-100 Indonesian government PDFs from JDIH portals  
**Status:** Week 1 - Manual Download Approach  
**Target:** 50 documents minimum

---

## 🎯 Download Strategy

### Target Distribution (50 documents)

| Category | Documents | Priority | Examples |
|----------|-----------|----------|----------|
| **Civil Administration** | 15 | HIGH | KTP, KK, Akta Kelahiran |
| **Employment** | 10 | HIGH | Ketenagakerjaan, UMP |
| **Business Licensing** | 10 | MEDIUM | SIUP, NIB, Perizinan |
| **Social Assistance** | 10 | MEDIUM | Bansos, BPJS, JKN |
| **General Governance** | 5 | LOW | Pemerintahan, Otonomi Daerah |

---

## 🌐 JDIH Portals (Verified Access)

### 1. BPK (Badan Pemeriksa Keuangan)
**URL:** https://jdih.bpk.go.id/  
**Categories:** Keuangan negara, Audit, Perpres  
**Target:** 5 documents

**How to download:**
1. Go to https://jdih.bpk.go.id/
2. Search for documents (e.g., "Perpres Audit")
3. Click document → Download PDF
4. Save to `data/documents/pdfs/`
5. Note metadata (title, number, year, type)

---

### 2. Kemenkeu (Kementerian Keuangan)
**URL:** https://jdih.kemenkeu.go.id/  
**Categories:** Pajak, APBN, Keuangan  
**Target:** 5 documents

---

### 3. Kemnaker (Kementerian Ketenagakerjaan)
**URL:** https://jdih.kemnaker.go.id/  
**Categories:** Ketenagakerjaan, UMP, K3  
**Target:** 10 documents

---

### 4. Kemendagri (Kementerian Dalam Negeri)
**URL:** https://jdih.kemendagri.go.id/  
**Categories:** KTP, KK, Kependudukan  
**Target:** 15 documents (HIGH PRIORITY)

---

### 5. Kemkes (Kementerian Kesehatan)
**URL:** https://jdih.kemkes.go.id/  
**Categories:** BPJS, JKN, Kesehatan  
**Target:** 5 documents

---

### 6. OJK (Otoritas Jasa Keuangan)
**URL:** https://jdih.ojk.go.id/  
**Categories:** Perbankan, Asuransi  
**Target:** 5 documents

---

### 7. Jakarta
**URL:** https://jdih.jakarta.go.id/  
**Categories:** Perda DKI, Pemprov  
**Target:** 5 documents

---

## 📝 Document Types Priority

### High Priority (Focus on these)
- **Perpres** (Peraturan Presiden) - Presidential Regulations
- **PP** (Peraturan Pemerintah) - Government Regulations  
- **Permen** (Peraturan Menteri) - Ministerial Regulations

### Medium Priority
- **UU** (Undang-Undang) - Laws
- **Kepres** (Keputusan Presiden) - Presidential Decrees
- **Kepmen** (Keputusan Menteri) - Ministerial Decrees

### Lower Priority (if have time)
- **Perda** (Peraturan Daerah) - Regional Regulations
- **SE** (Surat Edaran) - Circulars

---

## 🔍 Search Terms (Indonesian)

Copy-paste these into JDIH search:

### Civil Administration
- "KTP elektronik"
- "Kartu Keluarga"
- "Akta kelahiran"
- "Kependudukan"
- "Administrasi kependudukan"

### Employment
- "Ketenagakerjaan"
- "Upah minimum"
- "Keselamatan kerja"
- "Jamsostek"
- "BPJS Ketenagakerjaan"

### Business Licensing
- "Perizinan usaha"
- "SIUP"
- "Nomor Induk Berusaha"
- "OSS"
- "Izin usaha"

### Social Assistance
- "Bantuan sosial"
- "BPJS Kesehatan"
- "JKN"
- "Kartu Indonesia Pintar"
- "PKH"

---

## 📋 Download Checklist

### Before Downloading
- [ ] Create `data/documents/pdfs/` folder
- [ ] Open `data/documents/metadata.json` for tracking
- [ ] Have spreadsheet ready for quick notes

### For Each Document
- [ ] Download PDF to `data/documents/pdfs/`
- [ ] Rename file: `{Type}_{Number}_{Year}_{Title}.pdf`
- [ ] Record metadata:
  - Title
  - Document type (Perpres, PP, etc.)
  - Number
  - Year
  - Category
  - Portal source
  - URL (if available)

### After Downloading
- [ ] Reached 50+ documents
- [ ] All 5 categories represented
- [ ] Metadata.json updated
- [ ] Files organized in pdfs/ folder

---

## 📄 Naming Convention

**Format:** `{Type}_{Number}_{Year}_{Short_Title}.pdf`

**Examples:**
- `Perpres_26_2009_KTP_Elektronik.pdf`
- `PP_40_2019_BPJS_Kesehatan.pdf`
- `Permen_13_2020_Ketenagakerjaan.pdf`

**Rules:**
- No spaces (use underscores)
- Max 100 characters
- Remove special characters
- Keep it descriptive but concise

---

## 📊 Metadata Template

Update `data/documents/metadata.json` after each download:

```json
{
  "version": "1.0",
  "created": "2024-12-17",
  "total_documents": 50,
  "documents": [
    {
      "title": "Peraturan Presiden tentang KTP Elektronik",
      "type": "Perpres",
      "number": "26",
      "year": "2009",
      "category": "civil_administration",
      "portal": "kemendagri",
      "url": "https://jdih.kemendagri.go.id/...",
      "file_path": "data/documents/pdfs/Perpres_26_2009_KTP_Elektronik.pdf",
      "download_date": "2024-12-17T14:00:00"
    }
  ]
}
```

---

## ⏱️ Time Estimate

- **Per document:** 2-3 minutes (find, download, rename, record)
- **50 documents:** 100-150 minutes (~2-2.5 hours)
- **Recommendation:** Break into 2-3 sessions

**Session 1:**  
Civil Administration (15 docs) - 30-45 min

**Session 2:**  
Employment + Business (20 docs) - 40-60 min

**Session 3:**  
Social Assistance + Governance (15 docs) - 30-45 min

---

## ✅ Quality Checks

Before marking complete:

- [ ] All PDFs are text-based (not scanned images)
- [ ] Files open without errors
- [ ] File sizes reasonable (50KB - 5MB typical)
- [ ] Filenames match convention
- [ ] Metadata complete for all docs
- [ ] All 5 categories represented

---

## 🚨 Common Issues & Solutions

### Issue: PDF is scanned image (no selectable text)
**Solution:** Skip it, find another document. We need text-extractable PDFs.

### Issue: Download link broken
**Solution:** Try another portal or search for same regulation elsewhere.

### Issue: Document in English (not Indonesian)
**Solution:** Skip it. We need Indonesian language documents.

### Issue: Very large file (>10MB)
**Solution:** Probably includes images/scans. Check if text-extractable, otherwise skip.

---

## 📈 Progress Tracking

Update this as you go:

```
Civil Administration:    [███░░░░░░░] 15/15
Employment:              [░░░░░░░░░░] 0/10
Business Licensing:      [░░░░░░░░░░] 0/10
Social Assistance:       [░░░░░░░░░░] 0/10
General Governance:      [░░░░░░░░░░] 0/5

Total:                   [███░░░░░░░] 15/50 (30%)
```

---

## 🎯 Success Criteria

- ✅ 50+ documents downloaded
- ✅ All 5 categories represented
- ✅ Metadata complete and accurate
- ✅ PDFs text-extractable (not scans)
- ✅ Organized file structure
- ✅ Ready for preprocessing (Week 1 next step)

---

**Created:** 2024-12-17  
**Status:** Ready for manual download  
**Estimated Time:** 2-3 hours  
**Next Step:** Update metadata.json and run preprocessing
