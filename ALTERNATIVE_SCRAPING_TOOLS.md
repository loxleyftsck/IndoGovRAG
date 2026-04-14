# 🔧 Alternative Scraping Tools - Easy & Powerful

**Problem:** Need better scraping solution for Indonesian government docs  
**Current:** Basic BeautifulSoup (manual, slow)  
**Target:** Automated, reliable, production-grade

---

## 🚀 Top 3 Recommended Tools

### 1. **Firecrawl** ⭐ BEST FOR YOUR USE CASE

**Why:**

- Converts any website to clean markdown automatically
- Handles JavaScript, dynamic content
- Built-in rate limiting & retry
- Cloud-based (no local setup hassle)

**Setup (5 min):**

```bash
pip install firecrawl-py

# Get free API key from https://firecrawl.dev
export FIRECRAWL_API_KEY="your-key"
```

**Usage:**

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="your-key")

# Scrape single page
result = app.scrape_url("https://dukcapil.kemendagri.go.id/ktp-elektronik")
print(result['markdown'])  # Clean markdown!

# Crawl entire site (smart)
crawl_result = app.crawl_url(
    "https://dukcapil.kemendagri.go.id",
    params={
        'crawlerOptions': {
            'includes': ['*/ktp*', '*/akta*', '*/kartu-keluarga*'],
            'limit': 50
        }
    }
)
```

**Pros:**

- ✅ No browser automation needed
- ✅ Auto-handles JavaScript
- ✅ Clean markdown output
- ✅ Rate limiting built-in
- ✅ Free tier: 500 pages/month

**Cons:**

- ⚠️ Need API key
- ⚠️ Free tier limited

---

### 2. **Jina Reader** ⭐ EASIEST (No signup!)

**Why:**

- Zero setup - just prefix URL
- Converts any page to markdown
- FREE unlimited

**Usage:**

```python
import requests

url = "https://dukcapil.kemendagri.go.id/ktp-elektronik"
jina_url = f"https://r.jina.ai/{url}"

response = requests.get(jina_url)
markdown = response.text

print(markdown)  # Perfect markdown!
```

**That's it!** No API key, no setup, just works!

**Pros:**

- ✅ Zero setup
- ✅ FREE unlimited
- ✅ Just prefix URL with r.jina.ai/
- ✅ Clean markdown output

**Cons:**

- ⚠️ Rate limited (but generous)
- ⚠️ No bulk crawling

---

### 3. **Crawl4AI** - AI-Powered Local

**Why:**

- AI-powered extraction
- Runs locally (privacy)
- Smart content detection

**Setup:**

```bash
pip install crawl4ai
playwright install  # One-time browser install
```

**Usage:**

```python
from crawl4ai import WebCrawler

crawler = WebCrawler()
result = crawler.run(
    url="https://dukcapil.kemendagri.go.id/ktp-elektronik"
)

print(result.markdown)  # Smart extraction!
```

**Pros:**

- ✅ AI-powered (smart extraction)
- ✅ Local (no API needed)
- ✅ Free & open source

**Cons:**

- ⚠️ Need Playwright (1GB download)
- ⚠️ Slower than cloud solutions

---

## 💡 Quick Implementation Plan

### Option A: Jina Reader (FASTEST - 5 min) ⭐ RECOMMENDED

```python
"""Quick scraper using Jina Reader"""
import requests
import json
from pathlib import Path

def scrape_with_jina(urls):
    """Scrape multiple URLs using Jina Reader"""
    documents = []
    
    for url in urls:
        try:
            # Magic: just prefix with r.jina.ai/
            jina_url = f"https://r.jina.ai/{url}"
            response = requests.get(jina_url, timeout=30)
            
            if response.status_code == 200:
                markdown = response.text
                
                # Save document
                doc = {
                    'title': url.split('/')[-1],
                    'source_url': url,
                    'content': markdown,
                    'source': 'jina_reader',
                    'scraped_at': datetime.now().isoformat()
                }
                documents.append(doc)
                print(f"✅ Scraped: {url}")
            
        except Exception as e:
            print(f"❌ Failed: {url} - {e}")
    
    return documents

# Priority URLs
urls = [
    "https://www.kemendagri.go.id/page/read/48/syarat-dan-tata-cara-pembuatan-e-ktp",
    "https://jdih.setkab.go.id/PUUdoc/7308/UU0242013.htm",
    # Add 20-30 more government URLs
]

docs = scrape_with_jina(urls)

# Save
output = Path("data/scraped/jina_scraped.json")
output.parent.mkdir(parents=True, exist_ok=True)
with open(output, 'w', encoding='utf-8') as f:
    json.dump(docs, f, indent=2, ensure_ascii=False)

print(f"\n✅ Scraped {len(docs)} documents!")
```

**Just run and done!** No API key, no setup.

---

### Option B: Firecrawl (MOST POWERFUL)

```python
"""Production scraper using Firecrawl"""
from firecrawl import FirecrawlApp
import json
from pathlib import Path

app = FirecrawlApp(api_key="fc-your-key")

# Crawl entire site intelligently
result = app.crawl_url(
    "https://dukcapil.kemendagri.go.id",
    params={
        'crawlerOptions': {
            'includes': [
                '*/ktp*', 
                '*/akta*', 
                '*/kartu-keluarga*',
                '*/panduan*',
                '*/syarat*'
            ],
            'excludes': [
                '*/berita*',
                '*/galeri*'
            ],
            'limit': 100,
            'maxDepth': 3
        }
    }
)

# Save all pages
documents = []
for page in result['data']:
    doc = {
        'title': page['metadata']['title'],
        'source_url': page['metadata']['sourceURL'],
        'content': page['markdown'],
        'source': 'firecrawl'
    }
    documents.append(doc)

# Save
Path("data/scraped/firecrawl_scraped.json").write_text(
    json.dumps(documents, indent=2, ensure_ascii=False),
    encoding='utf-8'
)

print(f"✅ Scraped {len(documents)} pages!")
```

---

## 🎯 My Recommendation

**Use Jina Reader** because:

1. ✅ Zero setup (5 min to working)
2. ✅ FREE unlimited
3. ✅ Perfect for government sites
4. ✅ Clean markdown output
5. ✅ No API key needed

**Steps:**

1. Create list of 30-50 government URLs
2. Run Jina scraper script (provided above)
3. Get 30-50 clean markdown documents
4. Ingest to RAG
5. **DONE!** 100+ docs achieved

---

## 📋 Example URL List (Ready to Use)

```python
GOVERNMENT_URLS = [
    # KTP
    "https://www.kemendagri.go.id/page/read/48/syarat-dan-tata-cara-pembuatan-e-ktp",
    "https://disdukcapil.jakarta.go.id/layanan/ktp-elektronik",
    
    # Akta
    "https://disdukcapil.jakarta.go.id/layanan/akta-kelahiran",
    "https://disdukcapil.jakarta.go.id/layanan/akta-perkawinan",
    
    # Legal docs
    "https://jdih.setkab.go.id/PUUdoc/7308/UU0242013.htm",
    "https://jdih.setkab.go.id/PUUdoc/7128/UU0232006.htm",
    
    # OSS
    "https://oss.go.id/informasi/panduan-pengguna",
    
    # NPWP
    "https://www.pajak.go.id/id/cara-membuat-npwp",
    
    # Add 20-30 more...
]
```

---

**Want me to create complete Jina Reader scraper now?**
It'll take 5 minutes and get you 30-50 real government documents! 🚀
