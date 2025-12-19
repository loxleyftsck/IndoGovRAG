# 🧪 Testing Guide - IndoGovRAG v1.0-alpha

**Last Updated:** 2024-12-19  
**Version:** v1.0-alpha  
**Environment:** Local Development

---

## ✅ PRE-FLIGHT CHECKLIST

Before testing, ensure:

- [ ] Frontend running: `npm run dev` → http://localhost:3000
- [ ] Backend running: `python api/main.py` → http://localhost:8000
- [ ] `.env` file created with `GEMINI_API_KEY`
- [ ] 13 documents loaded in vector store
- [ ] No build errors in terminal

---

## 🚀 QUICK START TEST

### **1. Open Application**
```
URL: http://localhost:3000
Expected: Professional UI loads with example questions
```

### **2. Test Basic Query**
**Action:** Click example question "Bagaimana cara membuat SIM A?"

**Expected Result:**
- ⏳ Loading animation appears
- 🤖 AI-generated answer displays (natural Indonesian)
- 📚 Sources shown with match scores
- 💾 Query saved to history sidebar
- ⚡ Response time <3 seconds

### **3. Test AI Quality**
**Action:** Try custom query: "Berapa biaya membuat paspor?"

**Expected Result:**
- Answer mentions "Rp 100.000 - Rp 655.000"
- Cites official source (UU No. 6 Tahun 2011)
- Natural, conversational Indonesian
- No copy-paste text

---

## 🔒 SECURITY TESTS

### **Test 1: CSRF Protection**
**Open Browser Console:**
```javascript
// Try to query WITHOUT CSRF token
fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({question: 'test'})
})
```

**Expected:** ❌ 403 Forbidden (CSRF token missing)

---

### **Test 2: XSS Prevention**
**Try malicious query:**
```
<script>alert('XSS')</script>
```

**Expected:** 
- ✅ Query sanitized
- ✅ No script execution
- ✅ Safe text displayed

---

### **Test 3: Request Size Limit**
**Try huge payload:**
```javascript
fetch('http://localhost:8000/api/query', {
  method: 'POST',
  body: JSON.stringify({question: "A".repeat(1000000)})
})
```

**Expected:** ❌ 413 Payload Too Large

---

###Test 4: Input Validation**
**Try dangerous patterns:**
```
Query: "javascript:alert(1)"
Query: "../../../etc/passwd"
Query: "<iframe src='evil.com'>"
```

**Expected:** ❌ 400 Bad Request (Invalid input detected)

---

## 📊 FUNCTIONAL TESTS

### **Search Accuracy**

**Test Cases:**

| Query | Expected Document | Pass/Fail |
|-------|-------------------|-----------|
| "Apa itu KTP?" | KTP Elektronik | ⬜ |
| "Cara buat SKCK" | SKCK | ⬜ |
| "Berapa iuran BPJS?" | BPJS Kesehatan | ⬜ |
| "NIB untuk usaha" | NIB/OSS | ⬜ |
| "Akta kelahiran terlambat" | Akta Kelahiran | ⬜ |

---

### **UI/UX Tests**

**1. Example Questions**
- [ ] All 6 categories displayed
- [ ] Click triggers search
- [ ] Loading state shows

**2. History Sidebar**
- [ ] Queries saved to localStorage
- [ ] Max 10 items
- [ ] Click replays query
- [ ] "Hapus Riwayat" clears all

**3. Error Handling**
- [ ] Stop backend → Shows connection error
- [ ] Invalid query → Shows validation error
- [ ] Helpful suggestions provided

**4. Responsive Design**
- [ ] Mobile view works
- [ ] Tablet view works
- [ ] Desktop view optimal

---

## ⚡ PERFORMANCE TESTS

### **Response Time**

**Measure with Browser DevTools (Network tab):**

| Query Type | Target | Measured |
|------------|--------|----------|
| Simple (cached) | <500ms | ⬜ |
| Complex (first time) | <3s | ⬜ |
| With AI (Gemini) | <5s | ⬜ |

**How to test:**
1. Open DevTools → Network tab
2. Submit query
3. Check "api/query" request time
4. Record in table above

---

### **Load Test (Manual)**

**Action:** Submit 10 queries rapidly

**Expected:**
- ✅ Rate limit kicks in (~10-20/min)
- ✅ No crashes
- ✅ Error messages clear
- ✅ System recovers

---

## 🐛 REGRESSION TESTS

### **Previously Fixed Bugs:**

**1. Document Loading**
```bash
python scripts/add_session2_docs.py
```
**Expected:** ✅ 8 documents added successfully

**2. Frontend Build**
```bash
npm run build
```
**Expected:** ✅ No TypeScript errors

**3. Missing Imports**
- [ ] All Lucide icons render
- [ ] No console errors about missing modules

**4. History State**
- [ ] No "history.map is not a function" error
- [ ] History displays correctly

---

## 📝 MANUAL TEST SCENARIOS

### **Scenario 1: New User Journey**

**Steps:**
1. Open http://localhost:3000 (fresh browser)
2. Read landing page
3. Click "Identitas" category example
4. Review AI answer
5. Check sources
6. Try custom question
7. Review history sidebar

**Success Criteria:**
- [ ] UI intuitive
- [ ] Answers helpful
- [ ] Sources credible
- [ ] History functional

---

### **Scenario 2: Power User**

**Steps:**
1. Ask 5 different questions
2. Check all history items
3. Replay old query from history
4. Try edge cases (very short, very long)
5. Test all 6 categories

**Success Criteria:**
- [ ] All features work
- [ ] Performance consistent
- [ ] No crashes
- [ ] Data persists

---

### **Scenario 3: Malicious User**

**Steps:**
1. Try XSS payload
2. Try SQL injection (even though we use JSON)
3. Send 100 requests/minute
4. Send 1MB payload
5. Try CSRF attack

**Success Criteria:**
- [ ] All attacks blocked
- [ ] Audit logs generated
- [ ] System stable
- [ ] Graceful error messages

---

## 🎯 ACCEPTANCE CRITERIA

### **v1.0-alpha Sign-Off:**

- [ ] **Functional:** All core features work
- [ ] **Security:** All P0 vulnerabilities fixed
- [ ] **Performance:** Response time <5s
- [ ] **UI/UX:** Professional, polished
- [ ] **Stability:** No crashes in 30min testing
- [ ] **Documentation:** Complete README + guides

**If ALL checked:** ✅ **v1.0-alpha PASSED!**

---

## 🔧 TROUBLESHOOTING

### **Issue: API Not Responding**

**Check:**
```bash
# Backend running?
curl http://localhost:8000/api/health

# Expected: {"status":"healthy","documents_indexed":13}
```

**Fix:**
1. Restart backend: `python api/main.py`
2. Check `.env` file exists
3. Verify port 8000 not in use

---

### **Issue: No AI Answers (Fallback Text)**

**Check `.env`:**
```bash
# Must have:
GEMINI_API_KEY=AIzaSy...
```

**Fix:**
1. Get API key from https://makersuite.google.com
2. Add to `.env`
3. Restart backend

---

### **Issue: Frontend Build Errors**

**Check:**
```bash
npm install  # Reinstall dependencies
npm run dev  # Check for errors
```

**Common fixes:**
- Delete `.next` folder
- Clear `node_modules`, reinstall
- Check TypeScript errors

---

### **Issue: CSRF Token Errors**

**Symptom:** All queries return 403

**Fix:**
1. Check frontend fetches CSRF token on load
2. Check token included in headers
3. Clear browser cache
4. Restart both frontend + backend

---

## 📊 TEST REPORT TEMPLATE

```markdown
# Test Report - IndoGovRAG v1.0-alpha

**Date:** YYYY-MM-DD
**Tester:** [Your Name]
**Duration:** [Time spent]

## Summary
- Total Tests: __
- Passed: __
- Failed: __
- Blocked: __

## Pass/Fail
- [ ] Functional Tests
- [ ] Security Tests
- [ ] Performance Tests
- [ ] UI/UX Tests

## Issues Found
1. [Issue description]
2. [Issue description]

## Recommendation
[ ] PASS - Ready for deployment
[ ] FAIL - Needs fixes
```

---

## 🚀 NEXT STEPS AFTER TESTING

### **If All Tests Pass:**
1. ✅ Mark v1.0-alpha as stable
2. ✅ Create demo video
3. ✅ Polish README
4. ✅ Push to GitHub
5. ✅ Show to friends/recruiters!

### **If Tests Fail:**
1. 🐛 Document bugs
2. 🔧 Fix issues
3. 🔄 Re-test
4. ✅ Repeat until pass

---

**Happy Testing! 🧪**

Report any bugs to the dev team (that's you! 😄)
