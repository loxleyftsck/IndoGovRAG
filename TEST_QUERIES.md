# 🎯 Quick Test Queries for IndoGovRAG

Test these queries to verify your RAG system works perfectly!

---

## ✅ **RECOMMENDED TEST QUERIES**

### **Category: Identitas**

1. **"Cara membuat KTP elektronik baru"**
   - Should mention: Syarat, prosedur, gratis, Disdukcapil

2. **"Berapa lama proses pembuatan paspor?"**
   - Should mention: 3-7 hari kerja, biaya, dokumen

3. **"Cara membuat SKCK online"**
   - Should mention: Website, syarat, biaya Rp 30.000

### **Category: Transportasi**

4. **"Berapa biaya membuat SIM A 2024?"**
   - Should mention: Rp 120.000, masa berlaku 5 tahun

5. **"Cara perpanjang STNK online"**
   - Should mention: E-Samsat, biaya, prosedur

6. **"Syarat balik nama kendaraan bekas"**
   - Should mention: BPKB, STNK, BBNKB, cek fisik

### **Category: Ketenagakerjaan**

7. **"UMP Jakarta 2024 berapa?"**
   - Should mention: Rp 5.067.381

8. **"Cara daftar Kartu Prakerja"**
   - Should mention: prakerja.go.id, syarat, manfaat

### **Category: Properti**

9. **"Cara membuat sertifikat tanah baru"**
   - Should mention: BPN, syarat, biaya, prosedur

### **Category: Keluarga**

10. **"Syarat membuat akta kelahiran"**
    - Should mention: Dokumen ortu, surat lahir RS, gratis

---

## 🎯 **TEST FOR DIFFERENT SCENARIOS**

### **Simple Factual:**
- "Berapa biaya KTP?" → Should answer: Gratis
- "Masa berlaku paspor?" → Should answer: 5 tahun (biasa), 10 tahun (e-paspor)

### **How-To:**
- "Cara membuat..." → Should give step-by-step
- "Prosedur..." → Should list procedures

### **Requirements:**
- "Syarat..." → Should list requirements
- "Dokumen yang diperlukan..." → Should list documents

### **Cost:**
- "Berapa biaya..." → Should give exact amounts
- "Berapa harga..." → Should give price

---

## 📊 **EXPECTED RESPONSE QUALITY**

**Good Answer Characteristics:**
✅ Natural Indonesian language
✅ Specific numbers/costs
✅ Step-by-step when appropriate
✅ Mentions official sources
✅ Confident tone
✅ 2-4 sentences minimum

**Red Flags:**
❌ "Saya tidak tahu"
❌ Generic/vague answers
❌ Wrong information
❌ English instead of Indonesian
❌ Error messages

---

## 🚀 **QUICK START**

1. Open http://localhost:3000
2. Copy-paste query from above
3. Verify answer quality
4. Try 3-5 different queries
5. Take screenshots!

**Total Time:** 5-10 minutes

---

**Ready to test! 🎉**
