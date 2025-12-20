# 🐛 IndoGovRAG - Comprehensive Testing & Bug Hunting

**Purpose:** Final verification before portfolio showcase  
**Time:** 30-45 minutes  
**Objective:** Find and document any bugs or issues

---

## ✅ **TESTING CHECKLIST**

### **Phase 1: Basic Functionality (10 min)**

#### **1.1 Homepage Load**
- [ ] Page loads in <3 seconds
- [ ] No console errors (F12 → Console tab)
- [ ] All images load correctly
- [ ] CSS styling applied (no broken layout)
- [ ] Fonts render correctly

**Test:** Open http://localhost:3000

**Expected:**
- Clean interface
- "IndoGovRAG" title visible
- Search box prominent
- Sidebar present

**Bugs to Look For:**
- ❌ 404 errors in console
- ❌ Broken images
- ❌ Layout overflow/misalignment
- ❌ Missing styles

---

#### **1.2 Search Functionality**

**Test 1: Simple Query**
```
Query: "Berapa biaya membuat SIM A?"
```

**Checklist:**
- [ ] Query accepts input
- [ ] Search button responds to click
- [ ] Loading indicator appears
- [ ] Response appears in 2-5 seconds
- [ ] Answer is in Indonesian
- [ ] Sources shown below answer
- [ ] Relevance scores displayed (0-100%)
- [ ] No JavaScript errors

**Expected Answer Should Include:**
- Biaya: Rp 120.000
- Masa berlaku: 5 tahun
- Mention Samsat

**Bugs to Look For:**
- ❌ Query doesn't submit
- ❌ Infinite loading
- ❌ Error message instead of answer
- ❌ Empty response
- ❌ Sources not showing

---

**Test 2: Complex Query**
```
Query: "Bagaimana prosedur lengkap membuat paspor baru untuk pertama kali di Jakarta?"
```

**Checklist:**
- [ ] Handles long query (>50 characters)
- [ ] Returns comprehensive answer
- [ ] Multiple sources cited
- [ ] Answer coherent and relevant

**Bugs to Look For:**
- ❌ Truncated input
- ❌ Error on long query
- ❌ Irrelevant answer
- ❌ Generic response

---

**Test 3: Empty Query**
```
Query: [leave blank, click search]
```

**Expected:**
- Error message OR
- Disabled submit button

**Bugs to Look For:**
- ❌ Crash on empty submit
- ❌ API error in console
- ❌ No validation feedback

---

#### **1.3 Edge Cases**

**Test 4: Special Characters**
```
Query: "KTP <script>alert('xss')</script>"
```

**Expected:**
- XSS prevented (no alert popup)
- Query sanitized
- Normal search behavior

**Bugs to Look For:**
- ❌ XSS executed (alert shows)
- ❌ Raw HTML rendered
- ❌ Crash on special chars

---

**Test 5: Very Long Query**
```
Query: [Paste 3000+ characters]
```

**Expected:**
- Input validated (2000 char limit)
- Error message shown OR
- Query truncated gracefully

**Bugs to Look For:**
- ❌ Accepts unlimited input
- ❌ Backend crash
- ❌ Timeout error

---

**Test 6: SQL Injection Attempt**
```
Query: "' OR '1'='1"
```

**Expected:**
- Treated as normal query
- No database errors
- Safe handling

**Bugs to Look For:**
- ❌ SQL error in console
- ❌ Unexpected behavior
- ❌ Data leak

---

### **Phase 2: UI/UX Testing (10 min)**

#### **2.1 History Sidebar**

**Test:**
- [ ] Click on example query in sidebar
- [ ] Verify it populates search box
- [ ] Click different category
- [ ] Try multiple examples

**Checklist:**
- [ ] Examples are clickable
- [ ] Text populates correctly
- [ ] No duplicate entries
- [ ] Categories organized properly

**Bugs to Look For:**
- ❌ Click doesn't work
- ❌ Wrong text populated
- ❌ Sidebar collapses unexpectedly
- ❌ Overlapping text

---

#### **2.2 Responsive Design**

**Test:**
- [ ] Resize browser window (narrow/wide)
- [ ] Test on mobile size (F12 → Device Toolbar)
- [ ] Check tablet size (768px)

**Expected:**
- Layout adapts smoothly
- No horizontal scroll
- Text remains readable
- Buttons accessible

**Bugs to Look For:**
- ❌ Layout breaks <800px
- ❌ Text overflow
- ❌ Buttons off-screen
- ❌ Sidebar covers content

---

#### **2.3 Loading States**

**Test:**
- [ ] Submit query
- [ ] Observe loading indicator
- [ ] Note timing

**Expected:**
- Loading spinner/indicator visible
- Disabled submit during processing
- Clear when done

**Bugs to Look For:**
- ❌ No loading feedback
- ❌ Multiple submits possible
- ❌ Loading stuck/infinite
- ❌ Indicator doesn't disappear

---

### **Phase 3: Backend Testing (10 min)**

#### **3.1 API Endpoints**

**Test 1: CSRF Token**
```
1. Open DevTools (F12)
2. Network tab
3. Submit query
4. Check request headers
```

**Checklist:**
- [ ] CSRF token present in headers
- [ ] Token format: "X-CSRF-Token"
- [ ] Token changes per request

**Bugs to Look For:**
- ❌ No CSRF token sent
- ❌ Same token reused
- ❌ CSRF validation fails
- ❌ 403 Forbidden errors

---

**Test 2: API Response**

**Check Network Tab:**
```
POST /api/query
```

**Verify Response:**
- [ ] Status: 200 OK
- [ ] Content-Type: application/json
- [ ] Response time: <5 seconds
- [ ] JSON structure valid

**Expected JSON:**
```json
{
  "answer": "...",
  "sources": [...],
  "confidence": 0.85,
  "processing_time": 2.3
}
```

**Bugs to Look For:**
- ❌ 500 Internal Server Error
- ❌ 403 Forbidden
- ❌ Timeout (>10s)
- ❌ Malformed JSON
- ❌ Missing fields

---

**Test 3: Rate Limiting**

**Test:**
```
1. Submit 25 queries rapidly (within 1 minute)
2. Check for rate limit response
```

**Expected:**
- First 20: Success
- After 20: Rate limit error OR slower responses

**Bugs to Look For:**
- ❌ No rate limiting (unlimited queries)
- ❌ Server crash on spam
- ❌ Incorrect limit (should be 20/min)

---

#### **3.2 Error Handling**

**Test 1: Backend Down**
```
1. Stop backend: Ctrl+C on "python api/main.py" terminal
2. Try submitting query
```

**Expected:**
- Graceful error message
- "Server unavailable" or similar
- No app crash

**Bugs to Look For:**
- ❌ Blank screen
- ❌ Unhandled exception
- ❌ Page reload needed

**After Test:** Restart backend!

---

**Test 2: Invalid API Response**

**Simulate:**
```
Check browser console for any API errors during normal queries
```

**Expected:**
- No unhandled promise rejections
- Errors logged clearly
- User-friendly messages

**Bugs to Look For:**
- ❌ Unhandled rejection errors
- ❌ Technical errors shown to user
- ❌ Stack traces visible

---

### **Phase 4: Security Testing (10 min)**

#### **4.1 XSS Prevention**

**Test Cases:**
```
1. Query: "<img src=x onerror=alert('xss')>"
2. Query: "javascript:alert('xss')"
3. Query: "<iframe src='http://evil.com'></iframe>"
```

**Expected:**
- All sanitized
- No script execution
- Text displayed safely

**Bugs to Look For:**
- ❌ Alert popup (XSS executed)
- ❌ HTML injection
- ❌ Iframe loads

---

#### **4.2 CSRF Protection**

**Test:**
```
1. Open browser console
2. Try API call without CSRF token:
   fetch('http://localhost:8000/api/query', {
     method: 'POST',
     body: JSON.stringify({question: 'test'})
   })
```

**Expected:**
- 403 Forbidden (CSRF validation failed)

**Bugs to Look For:**
- ❌ Request succeeds without token
- ❌ No CSRF validation
- ❌ Token not required

---

#### **4.3 Input Validation**

**Test:**
```
Query: [2500 character string - exceeds 2000 limit]
```

**Expected:**
- Validation error
- "Query too long" message OR
- Input truncated at 2000 chars

**Bugs to Look For:**
- ❌ Accepts unlimited input
- ❌ Backend error
- ❌ No client-side validation

---

### **Phase 5: Performance Testing (5 min)**

#### **5.1 Response Times**

**Test 10 Different Queries:**
```
1. "Cara membuat KTP"
2. "Biaya SIM A"
3. "Syarat paspor"
4. "UMP Jakarta 2024"
5. "Prosedur balik nama kendaraan"
6. "Cara daftar Kartu Prakerja"
7. "Syarat sertifikat tanah"
8. "Biaya perpanjang STNK"
9. "Cara membuat akta kelahiran"
10. "BPJS Kesehatan cara daftar"
```

**Measure:**
- [ ] Average response time
- [ ] Slowest query
- [ ] Fastest query

**Target:**
- Average: <3 seconds
- 95th percentile: <5 seconds
- No query >10 seconds

**Bugs to Look For:**
- ❌ Any query >10 seconds
- ❌ Inconsistent performance
- ❌ Progressively slower (memory leak?)

---

#### **5.2 Memory Usage**

**Test:**
```
1. Open Task Manager (Ctrl+Shift+Esc)
2. Find browser process
3. Submit 20 queries
4. Check memory usage
```

**Expected:**
- Stable memory usage
- No significant leaks
- Browser responsive

**Bugs to Look For:**
- ❌ Memory constantly increasing
- ❌ Browser slowdown
- ❌ Tab crash

---

### **Phase 6: Content Quality (5 min)**

#### **6.1 Answer Accuracy**

**Test Queries with Known Answers:**

**Test 1:**
```
Query: "Berapa biaya membuat SIM A 2024?"
Expected: Rp 120.000
```
- [ ] Correct amount mentioned
- [ ] Masa berlaku (5 tahun) mentioned

**Test 2:**
```
Query: "UMP Jakarta 2024 berapa?"
Expected: Rp 5.067.381
```
- [ ] Exact amount correct

**Test 3:**
```
Query: "Berapa biaya membuat KTP?"
Expected: Gratis
```
- [ ] States it's free

**Bugs to Look For:**
- ❌ Wrong amounts
- ❌ Outdated information
- ❌ Generic "I don't know" answers

---

#### **6.2 Source Relevance**

**Test:**
```
For each query, check sources section
```

**Verify:**
- [ ] 4 sources shown
- [ ] Relevance scores >50%
- [ ] Top source >80% relevant
- [ ] Sources match query topic

**Bugs to Look For:**
- ❌ Irrelevant sources (wrong topic)
- ❌ All scores <50%
- ❌ Same source repeated
- ❌ No sources shown

---

## 🐛 **BUG REPORTING TEMPLATE**

When you find a bug, document it:

```markdown
## Bug #X: [Short Description]

**Severity:** [Critical / High / Medium / Low]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happened

**Screenshot/Error:**
[Paste error or screenshot]

**Browser/Environment:**
- Browser: Chrome 120
- OS: Windows 11
- URL: http://localhost:3000

**Frequency:**
- [ ] Always reproduces
- [ ] Sometimes (X%)
- [ ] Once only
```

---

## 📊 **TEST RESULTS SUMMARY**

After completing all tests:

```markdown
# Testing Results - IndoGovRAG v1.0-alpha

## Overall Grade: [A / B / C / D / F]

## Test Categories:
- Basic Functionality: [X/Y tests passed]
- UI/UX: [X/Y tests passed]
- Backend: [X/Y tests passed]
- Security: [X/Y tests passed]
- Performance: [X/Y tests passed]
- Content Quality: [X/Y tests passed]

## Bugs Found: [X total]
- Critical: X
- High: X
- Medium: X
- Low: X

## Critical Issues (Must Fix):
1. [Issue description]
2. [Issue description]

## Recommendations:
- [Recommendation 1]
- [Recommendation 2]

## Production Ready: [YES / NO / WITH FIXES]
```

---

## ✅ **COMPLETION CHECKLIST**

After testing:
- [ ] All basic functions work
- [ ] No critical security flaws
- [ ] Performance acceptable (<5s)
- [ ] No show-stopping bugs
- [ ] UI/UX smooth
- [ ] Content accurate

**If all checked:** ✅ **PRODUCTION-READY!**

---

## 🎯 **EXPECTED OUTCOME**

**Best Case:**
- All tests pass ✅
- 0-2 minor bugs found
- Production-ready confirmed

**Likely Case:**
- 90% tests pass ✅
- 3-5 minor bugs (UI tweaks)
- Production-ready with notes

**Worst Case:**
- <80% tests pass ❌
- Critical bugs found
- Need fixes before portfolio

---

**Start Testing!** 🐛🔍

**Time:** Set 30-minute timer and GO! ⏱️
