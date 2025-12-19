# 🧪 IndoGovRAG - Manual Testing & Screenshot Guide

**Purpose:** Test application functionality and capture portfolio screenshots  
**Time:** 10-15 minutes  
**Result:** Working demo proof + visual assets

---

## 📋 **TESTING CHECKLIST**

### **Step 1: Open Application**

**URL:** http://localhost:3000

**Verify:**
- ✅ Page loads completely
- ✅ "IndoGovRAG" title visible
- ✅ Search box prominent
- ✅ History sidebar on right
- ✅ Category examples shown
- ✅ Professional UI design

**Screenshot:** `01_homepage.png` (full page)

---

### **Step 2: Test Query #1 - KTP**

**Query:** "Cara membuat KTP baru"

**Action:**
1. Type in search box
2. Click "Cari" or press Enter
3. Wait 2-5 seconds

**Verify:**
- ✅ Loading indicator appears
- ✅ AI answer generated (Indonesian)
- ✅ Sources shown (4 documents)
- ✅ Relevance scores displayed (0-100%)
- ✅ Confidence indicator present
- ✅ Answer is coherent and relevant

**Expected Answer Should Include:**
- Syarat membuat KTP
- Prosedur/langkah-langkah
- Biaya (gratis)
- Dokumen yang diperlukan

**Screenshot:** `02_ktp_query.png` (full result)

---

### **Step 3: Test Query #2 - SIM**

**Query:** "Berapa biaya membuat SIM A 2024?"

**Action:**
1. Clear previous query
2. Type new query
3. Submit

**Verify:**
- ✅ Answer mentions specific cost (Rp 120.000)
- ✅ Sources cite SIM document
- ✅ High confidence score
- ✅ No errors

**Expected Answer Should Include:**
- Biaya exact: Rp 120.000
- Masa berlaku: 5 tahun
- Tempat pembuatan: Samsat
- Syarat (usia, dll)

**Screenshot:** `03_sim_query.png`

---

### **Step 4: Test Query #3 - Paspor**

**Query:** "Syarat membuat paspor baru"

**Verify:**
- ✅ Comprehensive answer
- ✅ Lists requirements (KTP, KK, Akta, foto)
- ✅ Sources relevant
- ✅ Processing time mentioned

**Screenshot:** `04_paspor_query.png`

---

### **Step 5: Test History Sidebar**

**Action:**
1. Click on example query in history sidebar
2. Verify it populates search box
3. Try different category

**Verify:**
- ✅ Examples clickable
- ✅ Categories organized
- ✅ Nice UI interaction

**Screenshot:** `05_history_sidebar.png` (focus on sidebar)

---

### **Step 6: Test Error Handling**

**Query:** "asdfghjkl random nonsense query"

**Verify:**
- ✅ Doesn't crash
- ✅ Graceful error message OR
- ✅ Generic response

**Screenshot:** `06_error_handling.png` (optional)

---

## 📸 **SCREENSHOT SPECIFICATIONS**

### **For Portfolio Use:**

**Format:** PNG (best quality)  
**Resolution:** Full HD (1920x1080) if possible  
**Focus:** Clear, readable text

### **Key Screenshots Needed:**

1. **Homepage (Hero Shot)**
   - Full interface visible
   - Clean, professional
   - Shows branding

2. **Query Result (Main Demo)**
   - AI answer clearly visible
   - Sources with scores
   - Clean result display

3. **Sources Detail**
   - Close-up of source citations
   - Relevance scores
   - Professional formatting

4. **UI Features**
   - History sidebar
   - Category examples
   - Modern design elements

---

## ✅ **QUALITY CHECKS**

After testing, verify:

**Functionality:**
- ✅ All queries return answers (no crashes)
- ✅ Response time <5 seconds
- ✅ Sources always present
- ✅ Answers in natural Indonesian
- ✅ UI responsive and smooth

**Content Quality:**
- ✅ Answers accurate (match documents)
- ✅ Sources relevant (high scores)
- ✅ No placeholder text
- ✅ Professional language

**Security:**
- ✅ No XSS (HTML properly escaped)
- ✅ CSRF token working (no errors)
- ✅ Input validation working
- ✅ No sensitive data exposed

---

## 📊 **TEST RESULTS TEMPLATE**

```markdown
# IndoGovRAG Test Results

**Date:** 2024-12-19  
**Version:** v1.0-alpha  
**Tester:** [Your Name]

## Test Summary
- Total Queries: 3+
- Success Rate: 100%
- Average Response Time: 3.2 seconds
- UI Performance: Excellent

## Query Results

### Query 1: "Cara membuat KTP baru"
- ✅ Answer Quality: Excellent
- ✅ Response Time: 2.8s
- ✅ Sources: 4 documents
- ✅ Top Score: 89%

### Query 2: "Berapa biaya membuat SIM A 2024?"
- ✅ Answer Quality: Perfect (exact cost mentioned)
- ✅ Response Time: 3.1s
- ✅ Sources: 4 documents
- ✅ Top Score: 95%

### Query 3: "Syarat membuat paspor baru"
- ✅ Answer Quality: Comprehensive
- ✅ Response Time: 3.5s
- ✅ Sources: 4 documents
- ✅ Top Score: 87%

## Issues Found
- None! ✅

## Overall Grade
**A** - Production-ready quality!
```

---

## 🎥 **BONUS: DEMO VIDEO (Optional)**

If you want to create a video demo:

**Tools:**
- **Windows:** Use Xbox Game Bar (Win + G)
- **Free:** OBS Studio
- **Pro:** Camtasia

**Script:**
1. Show homepage (5 sec)
2. Type query slowly (visible)
3. Show AI thinking/loading (2 sec)
4. Scroll through answer (3 sec)
5. Show sources (2 sec)
6. Repeat for 1-2 more queries
7. Total: 2-3 minutes max

**Tips:**
- Clean desktop
- Close unnecessary tabs
- Slow, deliberate actions
- No audio needed (add text later)

---

## 📁 **SAVE SCREENSHOTS TO:**

```
screenshots/
├── 01_homepage.png
├── 02_ktp_query.png
├── 03_sim_query.png
├── 04_paspor_query.png
└── 05_history_sidebar.png
```

Then add to README:
```markdown
## Screenshots

### Homepage
![Homepage](screenshots/01_homepage.png)

### AI-Powered Search
![Query Result](screenshots/02_ktp_query.png)
```

---

## ✅ **COMPLETION**

When done testing:
- ✅ 3+ queries tested successfully
- ✅ 3-5 screenshots captured
- ✅ No critical bugs found
- ✅ Ready for portfolio!

**Next:** Add screenshots to README and share! 🚀

---

**Happy Testing! 🎉**
