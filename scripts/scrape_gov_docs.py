#!/usr/bin/env python3
"""
IndoGovRAG Document Scraper - Production Grade
Scrapes Indonesian government documents from official sources

Target: Enrich corpus from 53 → 200-300 documents
Expected Impact: +40-50% answer quality improvement
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import hashlib

# PDF handling
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  pdfplumber not installed. PDF extraction disabled.")
    print("   Install: pip install pdfplumber")

class IndoGovScraper:
    """Main scraper class for Indonesian government documents"""
    
    def __init__(self, output_dir: str = "data/scraped"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IndoGovRAG-Research/1.0 (Educational Purpose)',
            'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8'
        })
        
        # Rate limiting (respectful scraping)
        self.rate_limit_delay = 2  # seconds between requests
        self.last_request_time = 0
        
        # Setup logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=log_dir / f"scraping_{datetime.now():%Y%m%d_%H%M%S}.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Cache to avoid re-scraping
        self.cache_file = self.output_dir / "scrape_cache.json"
        self.cache = self._load_cache()
        
        # Statistics
        self.stats = {
            'total_scraped': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'by_category': {}
        }
    
    def _load_cache(self) -> Dict:
        """Load scraping cache to avoid duplicates"""
        if self.cache_file.exists():
            with open(self.cache_file, encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save scraping cache"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _get_url_hash(self, url: str) -> str:
        """Generate hash for URL (cache key)"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch webpage with retry logic"""
        url_hash = self._get_url_hash(url)
        
        # Check cache
        if url_hash in self.cache:
            self.logger.info(f"Cache hit: {url}")
            self.stats['cached'] += 1
            return self.cache[url_hash]['content']
        
        # Fetch from web
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                content = response.text
                
                # Cache the result
                self.cache[url_hash] = {
                    'url': url,
                    'content': content,
                    'fetched_at': datetime.now().isoformat()
                }
                self._save_cache()
                
                self.logger.info(f"Successfully fetched: {url}")
                return content
                
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    self.stats['failed'] += 1
                    return None
    
    def extract_text_from_pdf(self, pdf_url: str) -> Optional[str]:
        """Extract text from PDF URL"""
        if not PDF_AVAILABLE:
            self.logger.warning("PDF extraction not available (install pdfplumber)")
            return None
        
        try:
            self._rate_limit()
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            # Save temporary PDF
            temp_pdf = self.output_dir / "temp.pdf"
            temp_pdf.write_bytes(response.content)
            
            # Extract text
            text_parts = []
            with pdfplumber.open(temp_pdf) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            # Cleanup
            temp_pdf.unlink()
            
            full_text = "\n\n".join(text_parts)
            self.logger.info(f"Extracted {len(full_text)} chars from PDF: {pdf_url}")
            return full_text
            
        except Exception as e:
            self.logger.error(f"PDF extraction failed for {pdf_url}: {e}")
            return None
    
    def scrape_indonesia_go_id(self, max_pages: int = 3) -> List[Dict]:
        """Scrape layanan publik from indonesia.go.id"""
        base_url = "https://indonesia.go.id"
        category_url = f"{base_url}/kategori/layanan-publik"
        
        documents = []
        
        for page in range(1, max_pages + 1):
            page_url = f"{category_url}?page={page}" if page > 1 else category_url
            
            html = self.fetch_page(page_url)
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find article links
            article_links = soup.select('article a[href], .article-list a[href]')
            
            for link in article_links[:10]:  # Limit per page
                article_url = urljoin(base_url, link.get('href'))
                
                # Skip if already scraped
                if self._get_url_hash(article_url) in self.cache:
                    continue
                
                article_html = self.fetch_page(article_url)
                if not article_html:
                    continue
                
                article_soup = BeautifulSoup(article_html, 'html.parser')
                
                # Extract content
                title = article_soup.select_one('h1, .article-title')
                title_text = title.get_text(strip=True) if title else "No title"
                
                content_div = article_soup.select_one('article .content, .article-content, .entry-content, .post-content')
                content_text = content_div.get_text(separator='\n', strip=True) if content_div else ""
                
                # Skip if too short or irrelevant
                if len(content_text) < 200:
                    continue
                
                # Determine category
                category = self._categorize_document(title_text, content_text)
                
                doc = {
                    'title': title_text,
                    'source_url': article_url,
                    'category': category,
                    'content': content_text,
                    'source': 'indonesia.go.id',
                    'doc_type': 'panduan_layanan',
                    'scraped_at': datetime.now().isoformat()
                }
                
                documents.append(doc)
                self.stats['successful'] += 1
                self.stats['total_scraped'] += 1
                self.stats['by_category'][category] = self.stats['by_category'].get(category, 0) + 1
                
                print(f"✓ Scraped: {title_text[:60]}... ({category})")
        
        return documents
    
    def _categorize_document(self, title: str, content: str) -> str:
        """Categorize document based on content"""
        text = (title + " " + content).lower()
        
        categories = {
            'ktp': ['ktp', 'e-ktp', 'kartu tanda penduduk', 'identitas'],
            'kk': ['kartu keluarga', ' kk '],
            'akta_kelahiran': ['akta kelahiran', 'kelahiran'],
            'akta_nikah': ['akta nikah', 'perkawinan', 'menikah'],
            'akta_kematian': ['akta kematian', 'kematian'],
            'izin_usaha': ['izin usaha', 'oss', 'nib', 'umkm', 'perizinan usaha'],
            'paspor': ['paspor', 'passport', 'imigrasi'],
            'visa': ['visa'],
            'npwp': ['npwp', 'pajak', 'spt'],
            'bpjs': ['bpjs', 'jaminan kesehatan'],
            'pendidikan': ['pendidikan', 'sekolah', 'universitas', 'kuliah'],
            'kesehatan': ['kesehatan', 'rumah sakit', 'puskesmas'],
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return 'umum'
    
    def save_documents(self, documents: List[Dict], prefix: str = "docs"):
        """Save scraped documents to JSON"""
        if not documents:
            print("⚠️  No documents to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{prefix}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved {len(documents)} documents to: {output_file}")
        return output_file
    
    def print_statistics(self):
        """Print scraping statistics"""
        print("\n" + "="*60)
        print("📊 SCRAPING STATISTICS")
        print("="*60)
        print(f"Total URLs processed: {self.stats['total_scraped']}")
        print(f"Successful: {self.stats['successful']} ✅")
        print(f"Failed: {self.stats['failed']} ❌")
        print(f"From cache: {self.stats['cached']} 💾")
        print("\nBy Category:")
        for category, count in sorted(self.stats['by_category'].items()):
            print(f"  {category}: {count}")
        print("="*60)

def main():
    """Main execution"""
    print("="*60)
    print("🚀 IndoGovRAG Document Scraper")
    print("="*60)
    print("Target: Enrich corpus from 53 → 200-300 documents")
    print("Sources: indonesia.go.id (layanan publik)")
    print("="*60 + "\n")
    
    scraper = IndoGovScraper()
    
    # Scrape from indonesia.go.id
    print("📥 Scraping from indonesia.go.id...")
    docs_indonesia = scraper.scrape_indonesia_go_id(max_pages=3)
    
    # TODO: Add more sources when ready
    # docs_oss = scraper.scrape_oss_go_id()
    # docs_kemendagri = scraper.scrape_kemendagri()
    # docs_jdih = scraper.scrape_jdih()
    
    # Combine all documents
    all_documents = docs_indonesia
    
    # Save results
    output_file = scraper.save_documents(all_documents, prefix="indonesiagov")
    
    # Print statistics
    scraper.print_statistics()
    
    print("\n✅ Scraping completed!")
    print(f"📁 Documents saved in: {scraper.output_dir}")
    print(f"📝 Log file: logs/scraping_*.log")
    
    if output_file:
        print(f"\n📋 Next steps:")
        print(f"1. Review scraped docs: cat {output_file}")
        print(f"2. Ingest to RAG: python scripts/ingest_documents.py --source {output_file}")
        print(f"3. Test improved answers!")

if __name__ == "__main__":
    main()
