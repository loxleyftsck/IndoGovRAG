# 🎯 Quick Test Script - 5 Minutes

**Fast verification before full bug hunting**

---

## ✅ **QUICK 5-MINUTE TEST**

### **1. Open App (10 seconds)**
```
URL: http://localhost:3000
```
**Check:** Loads without errors ✅/❌

---

### **2. Test 3 Queries (3 minutes)**

**Query 1:**
```
Berapa biaya membuat SIM A 2024?
```
**Expected:** Mentions Rp 120.000  
**Result:** ✅/❌

---

**Query 2:**
```
Cara membuat KTP baru
```
**Expected:** Step-by-step procedure  
**Result:** ✅/❌

---

**Query 3:**
```
UMP Jakarta 2024
```
**Expected:** Rp 5.067.381  
**Result:** ✅/❌

---

### **3. Check Console (30 seconds)**
```
Press F12 → Console tab
```
**Look for:** Red errors  
**Expected:** No errors  
**Result:** ✅/❌

---

### **4. Check Network (30 seconds)**
```
F12 → Network tab → Submit query
```
**Check:**
- POST /api/query: 200 OK ✅/❌
- Response time <5s ✅/❌
- CSRF token present ✅/❌

---

### **5. XSS Test (30 seconds)**
```
Query: <script>alert('test')</script>
```
**Expected:** No alert popup  
**Result:** ✅/❌

---

## 📊 **QUICK RESULT:**

**If all ✅:** Great! Proceed to full testing  
**If any ❌:** Note issues, fix if critical  

**Time:** 5 minutes total ⏱️

---

**Ready for full bug hunt? Use BUG_HUNTING_CHECKLIST.md!**
