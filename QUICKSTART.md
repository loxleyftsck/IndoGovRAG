# ✅ Quick Start Guide

**IndoGovRAG v1.0-alpha** - AI-Powered Indonesian Government Regulation Search

---

## ⚡ 5-Minute Setup

### **1. Prerequisites**
```bash
# Check versions
node --version  # Should be 18+
python --version  # Should be 3.11+
```

### **2. Install Dependencies**
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../
pip install -r requirements.txt
```

### **3. Configure Environment**
```bash
# Create .env file
cp .env.example .env

# Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" >> .env
```

**Get API Key:** https://makersuite.google.com/app/apikey (FREE!)

### **4. Run Application**

**Terminal 1 - Frontend:**
```bash
cd frontend
npm run dev
```
**→ http://localhost:3000**

**Terminal 2 - Backend:**
```bash
python api/main.py
```
**→ http://localhost:8000**

###**5. Test It!**
1. Open http://localhost:3000
2. Click any example question
3. See AI-powered answer! 🤖

---

## 🎯 What You Can Do

✅ Ask questions about Indonesian government regulations  
✅ Get AI-generated natural language answers  
✅ See source documents with citations  
✅ Save search history  
✅ Explore 13 government topics  

---

## 📚 Example Queries

Try these:
- "Bagaimana cara membuat SIM A?"
- "Berapa biaya membuat paspor?"
- "Syarat membuat akta kelahiran?"
- "Apa itu BPJS Kesehatan?"
- "Cara daftar NPWP online?"

---

## 🔒 Security Features

✅ CSRF Protection  
✅ XSS Sanitization  
✅ Input Validation  
✅ Request Size Limits  
✅ Security Headers  

**Security Grade:** A- (90/100)

---

## 🐛 Troubleshooting

**API not responding?**
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy"}
```

**No AI answers?**
- Check `.env` has `GEMINI_API_KEY`
- Restart backend: `python api/main.py`

**Frontend errors?**
```bash
rm -rf .next node_modules
npm install
npm run dev
```

---

## 📖 Full Documentation

- `README.md` - Project overview & features
- `TESTING.md` - Complete testing guide
- `ROADMAP.md` - Development roadmap
- `SECURITY_FIXES.md` - Security details

---

## 🚀 Next Steps

**For Portfolio:**
- Create demo video (2-min)
- Add screenshots to README
- Push to GitHub

**For Production:**
- See `ROADMAP.md` for Path B (Beta) or Path C (Production)

---

**Built with ❤️ for Indonesia 🇮🇩**

Need help? Check the docs or open an issue!
