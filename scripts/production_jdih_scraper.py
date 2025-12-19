"""
Production JDIH Selenium Scraper
Full-featured scraper using Selenium for JavaScript-rendered sites
Downloads 50-100+ real government PDFs

Features:
- Selenium WebDriver (handles JS)
- Retry logic with exponential backoff
- PDF download and text extraction
- Robust error handling
- Progress tracking
- Database integration
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import time
import PyPDF2
import requests
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.retrieval.simple_vector_store import SimpleVectorStore


class ProductionJDIHScraper:
    """
    Production-grade JDIH scraper using Selenium
    
    Capabilities:
    - Handles JavaScript-rendered content
    - Downloads PDFs from multiple JDIH portals
    - Extracts and processes text
    - Adds to vector database
    - Comprehensive error handling
    """
    
    JDIH_PORTALS = {
        'kemnaker': {
            'url': 'https://jdih.kemnaker.go.id',
            'name': 'Kementerian Ketenagakerjaan',
            'category': 'ketenagakerjaan'
        },
        'kemenkeu': {
            'url': 'https://jdih.kemenkeu.go.id',
            'name': 'Kementerian Keuangan',
            'category': 'keuangan'
        },
        'bpk': {
            'url': 'https://peraturan.bpk.go.id',
            'name': 'Badan Pemeriksa Keuangan',
            'category': 'keuangan'
        },
        'atrbpn': {
            'url': 'https://jdih.atrbpn.go.id',
            'name': 'ATR/BPN',
            'category': 'pertanahan'
        }
    }
    
    def __init__(self, headless=True, max_docs=50):
        """
        Initialize scraper
        
        Args:
            headless: Run browser in headless mode
            max_docs: Maximum documents to download
        """
        self.headless = headless
        self.max_docs = max_docs
        self.download_dir = Path("data/documents/pdfs")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.driver = None
        self.downloaded_count = 0
        self.failed_count = 0
        self.documents = []
        
        print("🔧 Initializing Production JDIH Scraper...")
        print(f"   Download directory: {self.download_dir}")
        print(f"   Target documents: {max_docs}")
        print(f"   Headless mode: {headless}")
    
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        print("\n🌐 Setting up Chrome WebDriver...")
        
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Set download preferences
            prefs = {
                "download.default_directory": str(self.download_dir.absolute()),
                "download.prompt_for_download": False,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Use webdriver-manager to auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            print("   ✅ WebDriver ready!")
            
        except Exception as e:
            print(f"   ❌ Error setting up driver: {e}")
            raise
    
    def scrape_portal(self, portal_key: str, limit: int = 20) -> List[Dict]:
        """
        Scrape a specific JDIH portal
        
        Args:
            portal_key: Portal identifier (e.g., 'kemnaker')
            limit: Maximum documents to find
        
        Returns:
            List of document metadata
        """
        if portal_key not in self.JDIH_PORTALS:
            print(f"❌ Unknown portal: {portal_key}")
            return []
        
        portal = self.JDIH_PORTALS[portal_key]
        
        print(f"\n🔍 Scraping: {portal['name']}")
        print(f"   URL: {portal['url']}")
        
        documents = []
        
        try:
            # Navigate to portal
            self.driver.get(portal['url'])
            
            # Wait for page load
            time.sleep(3)
            
            # Find PDF links (common patterns)
            pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            
            print(f"   Found {len(pdf_links)} PDF links")
            
            for i, link in enumerate(pdf_links[:limit]):
                try:
                    url = link.get_attribute('href')
                    text = link.text.strip() or link.get_attribute('title') or f"Document {i+1}"
                    
                    documents.append({
                        'title': text,
                        'url': url,
                        'portal': portal_key,
                        'category': portal['category'],
                        'source': portal['name']
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Error extracting link {i}: {e}")
                    continue
            
            print(f"   ✅ Extracted {len(documents)} document URLs")
            
        except TimeoutException:
            print(f"   ❌ Timeout loading {portal['url']}")
        except Exception as e:
            print(f"   ❌ Error scraping: {e}")
        
        return documents
    
    def download_pdf(self, url: str, filename: str, max_retries=3) -> str:
        """
        Download PDF with retry logic
        
        Args:
            url: PDF URL
            filename: Save filename
            max_retries: Maximum retry attempts
        
        Returns:
            Filepath if successful, None otherwise
        """
        filepath = self.download_dir / filename
        
        for attempt in range(max_retries):
            try:
                print(f"      📥 Downloading (attempt {attempt+1}/{max_retries})...")
                
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = filepath.stat().st_size
                print(f"         ✅ Downloaded ({file_size // 1024} KB)")
                
                return str(filepath)
                
            except Exception as e:
                print(f"         ⚠️ Attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        print(f"         ❌ Failed after {max_retries} attempts")
        return None
    
    def extract_text_from_pdf(self, pdf_path: str, max_pages=20) -> str:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to extract
        
        Returns:
            Extracted text (or None if failed)
        """
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                total_pages = len(reader.pages)
                pages_to_extract = min(max_pages, total_pages)
                
                text = ""
                for i in range(pages_to_extract):
                    page = reader.pages[i]
                    text += page.extract_text() + "\n\n"
                
                text = text.strip()
                
                if len(text) < 200:
                    print(f"         ⚠️ Text too short ({len(text)} chars), likely extraction failed")
                    return None
                
                print(f"         ✅ Extracted {len(text)} characters from {pages_to_extract} pages")
                return text
                
        except Exception as e:
            print(f"         ❌ Extraction error: {e}")
            return None
    
    def process_documents(self, documents: List[Dict]):
        """
        Download PDFs, extract text, add to database
        
        Args:
            documents: List of document metadata
        """
        vector_store = SimpleVectorStore()
        
        print(f"\n📚 Processing {len(documents)} documents...")
        print("=" * 70)
        
        for i, doc in enumerate(documents, 1):
            if self.downloaded_count >= self.max_docs:
                print(f"\n✋ Reached maximum ({self.max_docs} documents)")
                break
            
            print(f"\n[{i}/{len(documents)}] {doc['title'][:60]}...")
            
            # Generate safe filename
            safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' 
                                for c in doc['title'][:50])
            filename = f"{doc['portal']}_{safe_title}.pdf"
            
            # Download PDF
            filepath = self.download_pdf(doc['url'], filename)
            
            if not filepath:
                self.failed_count += 1
                continue
            
            # Extract text
            print(f"      📄 Extracting text...")
            text = self.extract_text_from_pdf(filepath)
            
            if not text:
                self.failed_count += 1
                continue
            
            # Add to vector store
            try:
                print(f"      💾 Adding to database...")
                
                vector_store.add_documents([{
                    'text': text,
                    'metadata': {
                        'title': doc['title'],
                        'source': doc['source'],
                        'category': doc['category'],
                        'portal': doc['portal'],
                        'url': doc['url'],
                        'pdf_path': filepath,
                        'scraped': True,
                        'scrape_date': datetime.now().isoformat()
                    }
                }])
                
                self.downloaded_count += 1
                self.documents.append(doc)
                
                print(f"      ✅ SUCCESS! ({self.downloaded_count}/{self.max_docs})")
                
                # Be respectful - delay between downloads
                time.sleep(2)
                
            except Exception as e:
                print(f"      ❌ Database error: {e}")
                self.failed_count += 1
    
    def run_full_scrape(self, portals: List[str] = None, docs_per_portal: int = 15):
        """
        Run full scraping workflow
        
        Args:
            portals: List of portal keys (None = all portals)
            docs_per_portal: Documents to download per portal
        """
        print("\n" + "=" * 70)
        print("🚀 PRODUCTION JDIH SCRAPER - FULL RUN")
        print("=" * 70)
        
        # Setup driver
        self.setup_driver()
        
        # Get initial document count
        vector_store = SimpleVectorStore()
        initial_count = vector_store.count()
        print(f"\n📊 Initial database: {initial_count} documents")
        
        # Determine portals to scrape
        if portals is None:
            portals = list(self.JDIH_PORTALS.keys())
        
        print(f"\n🎯 Target: {len(portals)} portals × {docs_per_portal} docs = {len(portals) * docs_per_portal} total")
        
        # Scrape each portal
        all_documents = []
        
        for portal_key in portals:
            docs = self.scrape_portal(portal_key, limit=docs_per_portal)
            all_documents.extend(docs)
            
            if self.downloaded_count >= self.max_docs:
                break
        
        print(f"\n📋 Total URLs found: {len(all_documents)}")
        
        # Process documents
        if all_documents:
            self.process_documents(all_documents)
        
        # Cleanup
        self.driver.quit()
        
        # Final report
        final_count = vector_store.count()
        
        print("\n" + "=" * 70)
        print("✅ SCRAPING COMPLETE!")
        print("=" * 70)
        print(f"Documents before:     {initial_count}")
        print(f"Successfully added:   {self.downloaded_count}")
        print(f"Failed:               {self.failed_count}")
        print(f"Documents after:      {final_count}")
        print(f"PDFs saved to:        {self.download_dir}")
        print("=" * 70)
        
        # Save metadata
        self.save_scraping_report()
    
    def save_scraping_report(self):
        """Save scraping report to JSON"""
        report = {
            'scrape_date': datetime.now().isoformat(),
            'total_downloaded': self.downloaded_count,
            'total_failed': self.failed_count,
            'documents': self.documents
        }
        
        report_path = Path("data/documents/scraping_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report saved: {report_path}")


def main():
    """Main execution"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                PRODUCTION JDIH SELENIUM SCRAPER                  ║
║                                                                  ║
║  Downloads REAL PDFs from Indonesian government JDIH portals    ║
║  Extracts text and adds to vector database                      ║
║                                                                  ║
║  Estimated time: 30-60 minutes for 50 documents                 ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Configuration
    MAX_DOCS = 50
    DOCS_PER_PORTAL = 15
    HEADLESS = True  # Set False to see browser
    
    # Portals to scrape (or None for all)
    PORTALS = ['kemnaker', 'atrbpn']  # Start with 2 portals
    
    print(f"\n⚙️  Configuration:")
    print(f"   Target documents: {MAX_DOCS}")
    print(f"   Per portal: {DOCS_PER_PORTAL}")
    print(f"   Headless: {HEADLESS}")
    print(f"   Portals: {', '.join(PORTALS)}")
    
    input("\n   Press ENTER to start scraping...")
    
    # Initialize and run
    scraper = ProductionJDIHScraper(headless=HEADLESS, max_docs=MAX_DOCS)
    
    try:
        scraper.run_full_scrape(portals=PORTALS, docs_per_portal=DOCS_PER_PORTAL)
        
        print("\n🎉 All done! Check data/documents/pdfs/ for downloaded PDFs")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        if scraper.driver:
            scraper.driver.quit()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if scraper.driver:
            scraper.driver.quit()
        raise


if __name__ == "__main__":
    main()
