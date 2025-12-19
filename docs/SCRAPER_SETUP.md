# Production JDIH Scraper - Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install selenium webdriver-manager PyPDF2
```

### 2. Run Scraper
```bash
python scripts/production_jdih_scraper.py
```

### 3. Wait for Completion
- Estimated time: 30-60 minutes for 50 documents
- PDFs saved to: `data/documents/pdfs/`
- Auto-added to vector database

---

## ⚙️ Configuration

Edit `production_jdih_scraper.py`:

```python
MAX_DOCS = 50              # Maximum documents to download
DOCS_PER_PORTAL = 15       # Per portal limit
HEADLESS = True            # False to see browser
PORTALS = ['kemnaker', 'atrbpn']  # Which portals
```

---

## 📊 Features

✅ Selenium WebDriver (handles JavaScript sites)
✅ Retry logic with exponential backoff
✅ PDF download and text extraction
✅ Automatic ChromeDriver installation
✅ Progress tracking
✅ Error handling
✅ Scraping report (JSON)

---

## 🎯 Supported Portals

- `kemnaker` - Kementerian Ketenagakerjaan
- `kemenkeu` - Kementerian Keuangan
- `bpk` - Badan Pemeriksa Keuangan
- `atrbpn` - ATR/BPN (Pertanahan)

---

## 📁 Output

```
data/documents/
├── pdfs/
│   ├── kemnaker_UU_13_2003.pdf
│   ├── kemnaker_PP_36_2021.pdf
│   └── ... (50+ files)
└── scraping_report.json
```

---

## ⚠️ Troubleshooting

### ChromeDriver Error
```bash
# Manually install ChromeDriver
# Download from: https://chromedriver.chromium.org/
```

### Permission Denied
```bash
# Run as administrator (Windows)
```

### Timeout Errors
```python
# Increase timeout in code
self.driver.set_page_load_timeout(60)  # 30 → 60
```

---

## 🔄 Resume Scraping

If interrupted, scraper will skip already downloaded PDFs (checks filename).

---

## 📈 Expected Results

**Successful Run:**
- 40-50 documents (80-100% success rate)
- 5-20 MB total PDF size
- Vector database: 18 → 60-70 documents

**Common Issues:**
- 5-10 failed downloads (network issues)
- 2-5 failed extractions (PDF corruption/scanned images)

---

## 🎉 Post-Scraping

After completion:
1. Check `data/documents/scraping_report.json` for details
2. Query vector store to test new documents
3. App automatically uses new documents!

---

## 🚨 IMPORTANT

- **Be respectful:** 2-second delay between requests
- **Check robots.txt:** Ensure compliance
- **For research/education:** Not for commercial scraping
- **Verify data:** Some PDFs may need manual review

---

Ready to run! 🚀
