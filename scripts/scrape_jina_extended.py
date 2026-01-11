"""
Extended Jina Reader Scraper - Target: 100+ Total Documents

Current: 68 docs (53 existing + 15 scraped)
Target: 100+ docs
This run: 50+ additional URLs
Expected result: 105-120 total docs (beta-ready!)
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time

# Extended URL list - Focus on missing topics and provinces
EXTENDED_GOVERNMENT_URLS = [
    # === SIM (Surat Izin Mengemudi) - NEW TOPIC ===
    "https://www.korlantas.polri.go.id/sim-online",
    "https://www.polri.go.id/layanan/sim",
    "https://jakarta.polisi.go.id/sim",
    
    # === STNK & BPKB - NEW TOPIC ===
    "https://www.korlantas.polri.go.id/stnk",
    "https://www.korlantas.polri.go.id/bpkb",
    
    # === Provincial Dukcapil - Jawa Barat ===
    "https://disdukcapil.jabarprov.go.id/portal/layanan/e-ktp",
    "https://disdukcapil.jabarprov.go.id/portal/layanan/kartu-keluarga",
    "https://disdukcapil.jabarprov.go.id/portal/layanan/akta-kelahiran",
    "https://disdukcapil.jabarprov.go.id/portal/layanan/akta-kematian",
    "https://disdukcapil.jabarprov.go.id/portal/layanan/akta-perkawinan",
    
    # === Provincial Dukcapil - Jawa Timur ===
    "https://dispendukcapil.jatimprov.go.id/site/layanan",
    "https://dispendukcapil.jatimprov.go.id/site/e-ktp",
    "https://dispendukcapil.jatimprov.go.id/site/kartu-keluarga",
    
    # === Provincial Dukcapil - Bali ===
    "https://disdukcapil.baliprov.go.id/layanan",
    "https://disdukcapil.baliprov.go.id/e-ktp",
    
    # === Provincial Dukcapil - Sumatera Utara ===
    "https://disdukcapil.sumutprov.go.id/layanan",
    
    # === Perpajakan Extended ===
    "https://www.pajak.go.id/id/spt-tahunan",
    "https://www.pajak.go.id/id/e-filing",
    "https://www.pajak.go.id/id/pkp-pengusaha-kena-pajak",
    "https://www.pajak.go.id/id/npwp-untuk-karyawan",
    
    # === OSS Extended ===
    "https://oss.go.id/portal/tentang-oss",
    "https://oss.go.id/portal/informasi/alur-perizinan",
    "https://oss.go.id/portal/sektor-usaha",
    
    # === Kemenkumham Extended ===
    "https://www.kemenkumham.go.id/layanan-publik/akta-notaris",
    "https://www.kemenkumham.go.id/layanan-publik/pendirian-pt",
    "https://www.kemenkumham.go.id/layanan-publik/pendirian-cv",
    
    # === Kemenaker (Ministry of Labor) ===
    "https://www.kemnaker.go.id/layanan/kartu-kuning",
    "https://www.kemnaker.go.id/layanan/jamsostek",
    
    # === Kemenkes (Health Ministry) ===
    "https://www.kemkes.go.id/layanan-publik/puskesmas",
    "https://www.kemkes.go.id/layanan-publik/rumah-sakit",
    
    # === Pendidikan (Education) ===
    "https://www.kemdikbud.go.id/layanan/kartu-indonesia-pintar",
    "https://www.kemdikbud.go.id/layanan/beasiswa",
    
    # === BPJS Extended ===
    "https://www.bpjsketenagakerjaan.go.id/layanan/jht",
    "https://www.bpjsketenagakerjaan.go.id/layanan/jkk",
    "https://www.bpjsketenagakerjaan.go.id/layanan/jkm",
    
    # === General Indonesia.go.id ===
    "https://indonesia.go.id/layanan/kependudukan/administrasi/ktp-elektronik",
    "https://indonesia.go.id/layanan/kependudukan/administrasi/akta-kelahiran",
    "https://indonesia.go.id/layanan/kependudukan/administrasi/kartu-keluarga",
    "https://indonesia.go.id/layanan/keuangan/pajak/cara-lapor-spt",
    "https://indonesia.go.id/layanan/bisnis-investasi/ekonomi/izin-usaha-online",
    
    # === Kemendagri Extended ===
    "https://www.kemendagri.go.id/pages/data-dan-informasi-kependudukan",
    "https://www.kemendagri.go.id/pages/pelayanan-terpadu-satu-pintu",
    
    # === Additional Provincial Sites ===
    "https://yogyakarta.go.id/layanan/administrasi-kependudukan",
    "https://www.jabarprov.go.id/layanan/dukcapil",
    "https://jatimprov.go.id/layanan/kependudukan",
]

def scrape_with_jina(url: str, max_retries: int = 3) -> dict:
    """Scrape URL using Jina Reader"""
    jina_url = f"https://r.jina.ai/{url}"
    
    for attempt in range(max_retries):
        try:
            print(f"  Fetching (attempt {attempt+1})...")
            response = requests.get(jina_url, timeout=30)
            
            if response.status_code == 200:
                markdown = response.text
                
                if len(markdown) < 100:
                    print(f"  ⚠️  Too short: {len(markdown)} chars")
                    continue
                
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
                print(f"  ⏱️  Rate limited, waiting...")
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
    
    if 'sim' in url_lower and ('korlantas' in url_lower or 'polri' in url_lower):
        return 'sim'
    elif 'stnk' in url_lower or 'bpkb' in url_lower:
        return 'stnk_bpkb'
    elif 'ktp' in url_lower or 'e-ktp' in url_lower:
        return 'ktp'
    elif 'akta-kelahiran' in url_lower or 'kelahiran' in url_lower:
        return 'akta_kelahiran'
    elif 'akta-perkawinan' in url_lower or 'perkawinan' in url_lower:
        return 'akta_nikah'
    elif 'akta-kematian' in url_lower:
        return 'akta_kematian'
    elif 'kartu-keluarga' in url_lower or '/kk' in url_lower:
        return 'kartu_keluarga'
    elif 'npwp' in url_lower or 'pajak' in url_lower or 'spt' in url_lower:
        return 'npwp'
    elif 'oss' in url_lower or 'izin' in url_lower or 'usaha' in url_lower or 'perizinan' in url_lower:
        return 'izin_usaha'
    elif 'paspor' in url_lower or 'imigrasi' in url_lower:
        return 'paspor'
    elif 'bpjs' in url_lower or 'jamsostek' in url_lower:
        return 'bpjs'
    elif 'pendidikan' in url_lower or 'beasiswa' in url_lower:
        return 'pendidikan'
    elif 'kesehatan' in url_lower or 'puskesmas' in url_lower:
        return 'kesehatan'
    elif 'notaris' in url_lower or 'pt' in url_lower or 'cv' in url_lower:
        return 'badan_usaha'
    else:
        return 'panduan_umum'

def main():
    """Main scraper execution"""
    print("="*60)
    print("🚀 EXTENDED Jina Reader Scraper - Round 2")
    print("="*60)
    print(f"Target: {len(EXTENDED_GOVERNMENT_URLS)} URLs")
    print("Goal: Reach 100+ total documents (beta-ready!)")
    print("="*60 + "\n")
    
    documents = []
    failed = []
    
    for i, url in enumerate(EXTENDED_GOVERNMENT_URLS, 1):
        print(f"\n[{i}/{len(EXTENDED_GOVERNMENT_URLS)}] {url[:60]}...")
        
        doc = scrape_with_jina(url)
        
        if doc:
            documents.append(doc)
            print(f"  ✅ Success: {doc['content_length']} chars ({doc['doc_type']})")
        else:
            failed.append(url)
            print(f"  ❌ Failed")
        
        # Polite delay
        if i < len(EXTENDED_GOVERNMENT_URLS):
            time.sleep(2)
    
    # Save results
    output_dir = Path("data/scraped")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"jina_extended_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    # Statistics
    print("\n" + "="*60)
    print("📊 EXTENDED SCRAPING COMPLETE")
    print("="*60)
    print(f"✅ Successful: {len(documents)}/{len(EXTENDED_GOVERNMENT_URLS)}")
    print(f"❌ Failed: {len(failed)}/{len(EXTENDED_GOVERNMENT_URLS)}")
    
    if documents:
        print(f"\n📄 Saved to: {output_file}")
        print(f"💾 Total size: {sum(d['content_length'] for d in documents):,} chars")
        
        # Category breakdown
        print(f"\n📊 By Category:")
        categories = {}
        for doc in documents:
            cat = doc['doc_type']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"   {cat}: {count} docs")
        
        print(f"\n🎯 Cumulative Total:")
        print(f"   Previous: 68 docs (53 existing + 15 first scrape)")
        print(f"   This run: {len(documents)} docs")
        print(f"   TOTAL: {68 + len(documents)} docs")
        
        if (68 + len(documents)) >= 100:
            print(f"\n   🎉 BETA MINIMUM REACHED! ({68 + len(documents)} >= 100)")
        else:
            gap = 100 - (68 + len(documents))
            print(f"\n   ⚠️  Need {gap} more docs for beta minimum")
    
    if failed:
        print(f"\n❌ Failed URLs ({len(failed)}):")
        for url in failed[:10]:
            print(f"   - {url}")
        if len(failed) > 10:
            print(f"   ... and {len(failed) - 10} more")
    
    print(f"\n{'='*60}")
    print("✅ Next step: Ingest to RAG")
    print(f"   python scripts/ingest_documents.py --source {output_file}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
