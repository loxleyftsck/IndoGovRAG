#!/usr/bin/env python3
"""
JDIH Scraper - Automated Government Document Collector
Scrapes legal documents from JDIH Sekretariat Kabinet
"""
import requests
from bs4 import BeautifulSoup
import time
import os
from pathlib import Path

BASE_URL = "https://jdih.setkab.go.id"
OUTPUT_DIR = Path("data/raw/phase2")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def scrape_document_list(category="undang-undang", limit=10):
    """
    Scrape list of documents from JDIH
    
    Args:
        category: Document category (undang-undang, peraturan-pemerintah, etc)
        limit: Maximum number of documents to scrape
    
    Returns:
        List of document metadata
    """
    print(f"🔍 Scraping category: {category}")
    
    url = f"{BASE_URL}/kategori/{category}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Note: Actual selectors need to be verified against real HTML
    # This is a template - adjust based on actual website structure
    documents = []
    
    # Example selector (NEEDS VERIFICATION):
    items = soup.find_all('div', class_='document-item', limit=limit)
    
    for item in items:
        try:
            doc = {
                'title': item.find('h3').text.strip() if item.find('h3') else 'Unknown',
                'pdf_url': item.find('a', href=True)['href'] if item.find('a', href=True) else None,
                'year': item.find('span', class_='year').text if item.find('span', class_='year') else '2024',
                'category': category
            }
            
            if doc['pdf_url']:
                documents.append(doc)
        except Exception as e:
            print(f"⚠️ Skipped item: {e}")
            continue
    
    print(f"   Found {len(documents)} documents")
    return documents

def download_pdf(url, output_path, retries=3):
    """
    Download PDF with retry logic
    
    Args:
        url: PDF URL
        output_path: Where to save
        retries: Number of retry attempts
    """
    for attempt in range(retries):
        try:
            print(f"   Downloading: {output_path.name}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"   ✅ Downloaded: {output_path.name}")
            time.sleep(1)  # Rate limiting
            return True
            
        except Exception as e:
            print(f"   ⚠️ Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"   ❌ Failed to download after {retries} attempts")
                return False

def main():
    """Main scraping workflow"""
    print("🚀 JDIH Document Scraper")
    print("=" * 60)
    
    categories = [
        "undang-undang",
        "peraturan-pemerintah",
        "peraturan-presiden"
    ]
    
    total_downloaded = 0
    
    for category in categories:
        documents = scrape_document_list(category, limit=10)
        
        for doc in documents:
            if not doc['pdf_url']:
                continue
            
            # Generate safe filename
            safe_title = "".join(c for c in doc['title'][:50] if c.isalnum() or c in (' ', '-', '_'))
            filename = f"{doc['category']}_{doc['year']}_{safe_title}.pdf"
            output_path = OUTPUT_DIR / filename
            
            # Skip if already downloaded
            if output_path.exists():
                print(f"   ⏭️ Already exists: {filename}")
                continue
            
            # Download
            if download_pdf(doc['pdf_url'], output_path):
                total_downloaded += 1
        
        print(f"✓ Completed category: {category}\n")
    
    print("=" * 60)
    print(f"🎉 Scraping complete!")
    print(f"   Total downloaded: {total_downloaded} documents")
    print(f"   Location: {OUTPUT_DIR}")
    print("\nNext step: python scripts/load_documents.py --input data/raw/phase2")

if __name__ == "__main__":
    main()
