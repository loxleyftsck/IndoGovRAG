"""
Jina Reader Scraper - Zero Setup, Instant Results!

Paling mudah: NO API KEY, NO SETUP, just run!
https://jina.ai/reader - Converts any URL to markdown
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time

# Priority Indonesian Government URLs
GOVERNMENT_URLS = [
    # === KTP & Administrasi Kependudukan ===
    "https://www.kemendagri.go.id/page/read/48/syarat-dan-tata-cara-pembuatan-e-ktp",
    "https://disdukcapil.jakarta.go.id/layanan/ktp-elektronik",
    "https://disdukcapil.bantenprov.go.id/layanan-adminduk/e-ktp",
    
    # === Akta Kelahiran ===
    "https://disdukcapil.jakarta.go.id/layanan/akta-kelahiran",
    "https://www.kemendagri.go.id/page/read/78/akta-kelahiran",
    
    # === Kartu Keluarga ===
    "https://disdukcapil.jakarta.go.id/layanan/kartu-keluarga",
    "https://www.kemendagri.go.id/page/read/79/kartu-keluarga",
    
    # === Akta Perkawinan & Perceraian ===
    "https://disdukcapil.jakarta.go.id/layanan/akta-perkawinan",
    "https://disdukcapil.jakarta.go.id/layanan/akta-perceraian",
    
    # === Legal Documents (UU) ===
    "https://jdih.setkab.go.id/PUUdoc/7308/UU0242013.htm",  # UU 24/2013 Adminduk
    "https://jdih.setkab.go.id/PUUdoc/7128/UU0232006.htm",  # UU 23/2006 Adminduk
    
    # === NPWP & Perpajakan ===
    "https://www.pajak.go.id/id/cara-membuat-npwp",
    "https://www.pajak.go.id/id/npwp-online",
    "https://www.pajak.go.id/id/informasi-umum/npwp",
    
    # === Izin Usaha & OSS ===
    "https://oss.go.id/informasi/panduan-pengguna",
    "https://oss.go.id/informasi/legalitas-berusaha",
    "https://www.kemenkopukm.go.id/panduan-oss-untuk-umkm",
    
    # === Paspor & Imigrasi ===
    "https://www.imigrasi.go.id/id/layanan-publik/paspor",
    "https://www.kemenkumham.go.id/layanan-publik/paspor-republik-indonesia",
    
    # === BPJS Kesehatan ===
    "https://www.bpjs-kesehatan.go.id/bpjs/index.php/pages/detail/2014/4",
    "https://www.bpjs-kesehatan.go.id/bpjs/pages/detail/2023/1/Syarat-dan-Tata-Cara-Pendaftaran",
    
    # === General Panduan ===
    "https://indonesia.go.id/kategori/layanan-publik",
    "https://www.jakarta.go.id/layanan",
]

def scrape_with_jina(url: str, max_retries: int = 3) -> dict:
    """
    Scrape URL using Jina Reader
    
    Magic: Just prefix URL with https://r.jina.ai/
    Returns clean markdown!
    """
    jina_url = f"https://r.jina.ai/{url}"
    
    for attempt in range(max_retries):
        try:
            print(f"  Fetching (attempt {attempt+1})...")
            response = requests.get(jina_url, timeout=30)
            
            if response.status_code == 200:
                markdown = response.text
                
                # Basic validation
                if len(markdown) < 100:
                    print(f"  ⚠️  Too short: {len(markdown)} chars")
                    continue
                
                # Extract title from first heading or URL
                title_line = [line for line in markdown.split('\n') if line.startswith('#')]
                title = title_line[0].strip('#').strip() if title_line else url.split('/')[-1]
                
                doc = {
                    'title': title,
                    'source_url': url,
                    'content': markdown,
                    'source': 'jina_reader',
                    'doc_type': categorize_url(url),
                    'scraped_at': datetime.now().isoformat(),
                    'content_length': len(markdown)
                }
                
                return doc
            
            elif response.status_code == 429:
                print(f"  ⚠️  Rate limited, waiting...")
                time.sleep(5 * (attempt + 1))
                
            else:
                print(f"  ❌ HTTP {response.status_code}")
                
        except requests.Timeout:
            print(f"  ⏱️  Timeout, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            break
    
    return None

def categorize_url(url: str) -> str:
    """Categorize document by URL"""
    url_lower = url.lower()
    
    if 'ktp' in url_lower or 'e-ktp' in url_lower:
        return 'ktp'
    elif 'akta-kelahiran' in url_lower or 'kelahiran' in url_lower:
        return 'akta_kelahiran'
    elif 'akta-perkawinan' in url_lower or 'perkawinan' in url_lower:
        return 'akta_nikah'
    elif 'kartu-keluarga' in url_lower or '/kk' in url_lower:
        return 'kartu_keluarga'
    elif 'npwp' in url_lower or 'pajak' in url_lower:
        return 'npwp'
    elif 'oss' in url_lower or 'izin' in url_lower or 'usaha' in url_lower:
        return 'izin_usaha'
    elif 'paspor' in url_lower or 'imigrasi' in url_lower:
        return 'paspor'
    elif 'bpjs' in url_lower:
        return 'bpjs'
    elif 'jdih' in url_lower or 'uu' in url_lower:
        return 'peraturan'
    else:
        return 'panduan_umum'

def main():
    """Main scraper execution"""
    print("="*60)
    print("🚀 Jina Reader Scraper - Indonesian Government Docs")
    print("="*60)
    print(f"Target: {len(GOVERNMENT_URLS)} URLs")
    print("Method: https://r.jina.ai/ (zero setup!)")
    print("="*60 + "\n")
    
    documents = []
    failed = []
    
    for i, url in enumerate(GOVERNMENT_URLS, 1):
        print(f"\n[{i}/{len(GOVERNMENT_URLS)}] {url[:60]}...")
        
        doc = scrape_with_jina(url)
        
        if doc:
            documents.append(doc)
            print(f"  ✅ Success: {doc['content_length']} chars ({doc['doc_type']})")
        else:
            failed.append(url)
            print(f"  ❌ Failed")
        
        # Polite delay
        if i < len(GOVERNMENT_URLS):
            time.sleep(2)
    
    # Save results
    output_dir = Path("data/scraped")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"jina_government_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    # Statistics
    print("\n" + "="*60)
    print("📊 SCRAPING COMPLETE")
    print("="*60)
    print(f"✅ Successful: {len(documents)}/{len(GOVERNMENT_URLS)}")
    print(f"❌ Failed: {len(failed)}/{len(GOVERNMENT_URLS)}")
    
    if documents:
        print(f"\n📄 Saved to: {output_file}")
        print(f"💾 Total size: {sum(d['content_length'] for d in documents):,} chars")
        
        # Category breakdown
        print(f"\n📊 By Category:")
        categories = {}
        for doc in documents:
            cat = doc['doc_type']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"   {cat}: {count} docs")
    
    if failed:
        print(f"\n❌ Failed URLs:")
        for url in failed:
            print(f"   - {url}")
    
    print(f"\n{'='*60}")
    print("✅ Next step: Ingest to RAG")
    print(f"   python scripts/ingest_documents.py --source {output_file}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
