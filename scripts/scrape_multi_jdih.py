"""
Production-quality JDIH multi-portal scraper.

Sources:
1. peraturan.bpk.go.id   - JDIH BPK. Has working search + pagination. 1994-2026.
2. jdih.atrbpn.go.id      - JDIH ATR/BPN. JSON-LD structured data.

Sitemap-based (from previous analysis):
- jdih.kemenkeu.go.id/sitemap.xml - 4,676 documents (metadata-only, no direct PDF)
- jdih.kemnaker.go.id/sitemap.xml - 2,312 documents (metadata-only, no direct PDF)

This script fetches structured content from accessible sources.
"""

import sys
import re
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data.chunker import DocumentChunker

BASE_DIR = Path("D:/IndoGov/IndoGovRAG")
DATA_DIR = BASE_DIR / "data" / "government_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 IndoGovRAG/1.0"
})

#  Source 1: peraturan.bpk.go.id 

def fetch_bpk_regulations(page: int = 1, page_size: int = 20) -> list[dict]:
    """Fetch regulation list from peraturan.bpk.go.id/search."""
    url = "https://peraturan.bpk.go.id/Search"
    params = {"keywords": "", "p": page, "ps": page_size}
    resp = session.get(url, params=params, timeout=20)
    if resp.status_code != 200:
        return []

    items = re.findall(
        r'<a href="/Details/(\d+)/[^"]+">\s*<div[^>]*>(.*?)</div>',
        resp.text, re.DOTALL
    )
    results = []
    for doc_id, html_block in items:
        # Extract title
        title_match = re.search(r'<h[56][^>]*>(.*?)</h[56]>', html_block, re.DOTALL)
        title = title_match.group(1).strip() if title_match else f"Doc {doc_id}"
        title = re.sub(r'<[^>]+>', '', title).strip()

        # Extract metadata lines
        metas = re.findall(r'<span[^>]*>(.*?)</span>', html_block, re.DOTALL)
        metas = [re.sub(r'<[^>]+>', '', m).strip() for m in metas if m.strip()]

        jenis = metas[0] if len(metas) > 0 else ""
        tahun = metas[1] if len(metas) > 1 else ""
        subjek = metas[2] if len(metas) > 2 else ""

        # Download PDF URL
        pdf_url = f"https://peraturan.bpk.go.id/Download/{doc_id}"

        results.append({
            "id": doc_id,
            "title": title,
            "jenis": jenis,
            "tahun": tahun,
            "subjek": subjek,
            "detail_url": f"https://peraturan.bpk.go.id/Details/{doc_id}",
            "pdf_url": pdf_url,
            "source": "BPK"
        })

    return results


def fetch_bpk_detail(doc_id: str) -> dict | None:
    """Fetch a single document detail page and extract abstract + PDF."""
    url = f"https://peraturan.bpk.go.id/Details/{doc_id}"
    resp = session.get(url, timeout=20)
    if resp.status_code != 200:
        return None

    text = resp.text

    # Extract abstract / description
    abstract_match = re.search(
        r'<div[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</div>',
        text, re.DOTALL
    )
    if not abstract_match:
        abstract_match = re.search(r'(?:Abstrak|Deskripsi|Ringkasan)[\s:]*</?[p]?(.*?)(?=<div|\Z)',
                                   text, re.DOTALL | re.IGNORECASE)
    abstract = ""
    if abstract_match:
        abstract = re.sub(r'<[^>]+>', '', abstract_match.group(1)).strip()

    # Extract PDF download link
    pdf_match = re.search(r'href="(/Download/\d+/[^"]+\.pdf)"', text)
    pdf_url = f"https://peraturan.bpk.go.id{pdf_match.group(1)}" if pdf_match else ""

    # Extract full text from paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', text, re.DOTALL)
    full_text = " ".join(
        re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs if len(p.strip()) > 50
    )

    return {"abstract": abstract[:500], "pdf_url": pdf_url, "full_text": full_text[:2000]}


def scrape_bpk(max_docs: int = 80, max_pages: int = 10) -> list[dict]:
    """Scrape regulations from peraturan.bpk.go.id."""
    all_docs = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        if len(all_docs) >= max_docs:
            break
        print(f"  [BPK] Fetching page {page}...", end=" ", flush=True)
        docs = fetch_bpk_regulations(page=page)
        new_docs = [d for d in docs if d["id"] not in seen_ids]
        if not new_docs:
            print("empty, stopping.")
            break
        for d in new_docs:
            seen_ids.add(d["id"])
        all_docs.extend(new_docs)
        print(f"got {len(new_docs)} docs (total: {len(all_docs)})")
        time.sleep(0.5)

        if len(all_docs) >= max_docs:
            break

    print(f"  [BPK] Fetched {len(all_docs)} document metadata.")
    return all_docs[:max_docs]


#  Source 2: jdih.atrbpn.go.id 

ATR_TYPES = ["uu-perppu", "pp", "perpres", "keppres", "inpres", "permen", "kepmen", "inmen", "perda", "se", "juknis"]


def fetch_atr_type_docs(doc_type: str, page: int = 1, per_page: int = 20) -> list[dict]:
    """Fetch document list from ATR/BPN by type."""
    url = f"https://jdih.atrbpn.go.id/peraturan/tipe/{doc_type}"
    params = {"page": page}
    resp = session.get(url, params=params, timeout=20)
    if resp.status_code != 200:
        return []

    text = resp.text

    # ATR/BPN list page has anchor tags: href="https://jdih.atrbpn.go.id/peraturan/detail/{id}/{slug}"
    # Grab full URLs with title text
    items = re.findall(
        r'href="(https://jdih\.atrbpn\.go\.id/peraturan/detail/\d+[^"]*)"\s*[^>]*>(.*?)</a>',
        text, re.DOTALL
    )

    results = []
    for detail_url, link_html in items:
        # Extract title text from the link HTML
        title = re.sub(r'<[^>]+>', '', link_html).strip()
        if not title:
            title = detail_url.split("/")[-1].replace("-", " ").title()

        doc_id_match = re.search(r'/detail/(\d+)', detail_url)
        doc_id = doc_id_match.group(1) if doc_id_match else ""

        # Extract year from title (4-digit number like 2021, 2022)
        year_match = re.search(r'\b(20\d{2})\b', title)
        tahun = year_match.group(1) if year_match else ""

        # Derive jenis from doc_type slug
        jenis_map = {
            "pp": "PP", "uu-perppu": "UU", "perpres": "Perpres",
            "keppres": "Keppres", "inpres": "Inpres", "permen": "Permen",
            "kepmen": "Kepmen", "inmen": "Inmen", "perda": "Perda",
            "se": "SE", "juknis": "Juknis"
        }

        results.append({
            "id": doc_id,
            "title": title,
            "jenis": jenis_map.get(doc_type, doc_type.upper()),
            "tahun": tahun,
            "subjek": doc_type,
            "detail_url": detail_url,
            "source": "ATR/BPN"
        })

    return results


def fetch_atr_detail(doc_id: str) -> dict | None:
    """Fetch ATR/BPN document detail page and extract JSON-LD + full text."""
    url = f"https://jdih.atrbpn.go.id/peraturan/detail/{doc_id}"
    resp = session.get(url, timeout=20)
    if resp.status_code != 200:
        return None

    text = resp.text

    # Extract JSON-LD
    ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL)
    json_ld = {}
    if ld_match:
        try:
            json_ld = json.loads(ld_match.group(1))
        except Exception:
            pass

    # Extract PDF link
    pdf_match = re.search(r'href="(/peraturan/download/\d+/[^"]+\.pdf)"', text)
    pdf_url = f"https://jdih.atrbpn.go.id{pdf_match.group(1)}" if pdf_match else ""

    # Extract full text
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', text, re.DOTALL)
    full_text = " ".join(
        re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs if len(p.strip()) > 50
    )

    description = ""
    if json_ld:
        description = json_ld.get("description", json_ld.get("abstract", ""))

    return {"json_ld": json_ld, "pdf_url": pdf_url, "full_text": full_text[:2000], "description": description[:500]}


def scrape_atrbpn(max_docs: int = 50) -> list[dict]:
    """Scrape regulations from jdih.atrbpn.go.id."""
    all_docs = []
    seen_ids = set()

    for doc_type in ATR_TYPES:
        if len(all_docs) >= max_docs:
            break
        print(f"  [ATR] Fetching type: {doc_type}...", end=" ", flush=True)
        docs = fetch_atr_type_docs(doc_type, page=1)
        new_docs = [d for d in docs if d["id"] not in seen_ids]
        for d in new_docs:
            seen_ids.add(d["id"])
        all_docs.extend(new_docs)
        print(f"got {len(new_docs)} docs (total: {len(all_docs)})")
        time.sleep(0.3)

    return all_docs[:max_docs]


#  Source 3: jdih.kemenkeu.go.id sitemap-based (metadata only) 

def load_kemenkeu_sitemap_urls(limit: int = 200) -> list[dict]:
    """Load document URLs from previously saved sitemap results."""
    sitemap_file = DATA_DIR.parent / "gov_sitemap_results.json"
    if not sitemap_file.exists():
        print("  [KMENKEU] Sitemap file not found, skipping.")
        return []

    with open(sitemap_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Navigate to Kemenkeu document URLs
    sections = data.get("source_data", {})
    kemenkeu_data = sections.get("jdih.kemenkeu.go.id", {})

    # Extract detail page URLs
    doc_pages = kemenkeu_data.get("document_detail_pages", {})
    all_urls = doc_pages.get("all_urls", [])[:limit]

    results = []
    for url in all_urls:
        # Extract slug to build title
        slug = url.split("/")[-1]
        title = slug.replace("-", " ").replace("/", " ").strip()

        # Try to extract document number from slug
        number_match = re.search(r'(?:nomor|no)[\s_-]?(\d+)', slug, re.IGNORECASE)
        year_match = re.search(r'(20\d{2}|19\d{2})', slug)
        number = number_match.group(1) if number_match else ""
        tahun = year_match.group(1) if year_match else ""

        results.append({
            "title": title.title(),
            "detail_url": url,
            "source": "Kemenkeu",
            "tahun": tahun,
            "number": number,
            "jenis": "PMK" if "pmk" in slug.lower() else ("KMK" if "kmk" in slug.lower() else "Peraturan"),
            "subjek": "Keuangan"
        })

    return results


#  Content Generation from Metadata 

def generate_structured_content(doc: dict) -> str:
    """Generate readable content from document metadata (used when no full text available)."""
    parts = []

    title = doc.get("title", "")
    if title:
        parts.append(f"[{doc.get('jenis', 'Dokumen')}] {title}")

    if doc.get("tahun"):
        parts.append(f"Tahun: {doc['tahun']}")

    if doc.get("subjek"):
        parts.append(f"Subjek: {doc['subjek']}")

    if doc.get("abstract"):
        parts.append(f"\nAbstrak:\n{doc['abstract']}")

    if doc.get("description"):
        parts.append(f"\nDeskripsi:\n{doc['description']}")

    # Add contextual Indonesian government content based on type
    jenis = doc.get("jenis", "").lower()

    context_templates = {
        "pmk": "Peraturan Menteri Keuangan ini mengatur mengenai {subjek}. Dokumen ini merupakan bagian dari regulasi keuangan negara yang diterbitkan oleh Kementerian Keuangan Republik Indonesia. Berlaku untuk seluruh wilayah Indonesia.",
        "kmk": "Keputusan Menteri Keuangan ini merupakan kebijakan teknis di bidang perpajakan, bea cukai, atau keuangan negara. Diterbitkan untuk mendukung implementasi regulasi.",
        "uu": "Undang-Undang ini merupakan produk hukum yang dikeluarkan oleh Dewan Perwakilan Rakyat bersama Pemerintah. Mengatur aspek tertentu dalam sistem hukum Indonesia.",
        "pp": "Peraturan Pemerintah ini merupakan regulasi turunan dari Undang-Undang. Diterbitkan untuk menjalankan ketentuan dalam Undang-Undang terkait.",
        "perpres": "Peraturan Presiden ini mengatur kebijakan tertentu di tingkat executive. Berlaku secara nasional.",
        "permen": "Peraturan Menteri ini mengatur teknis pelaksanaan di bidang terkait. Diterbitkan oleh Kementerian terkait.",
        "kepmen": "Keputusan Menteri ini merupakan keputusan teknis di bidang kewenangan Kementerian.",
    }

    if jenis in context_templates:
        subjek = doc.get("subjek", "regulasi terkait")
        parts.append(context_templates[jenis].format(subjek=subjek))

    parts.append(f"\nSumber: {doc.get('source', 'Unknown')} | {doc.get('detail_url', '')}")

    return "\n".join(parts)


#  Main 

def main():
    print("\n" + "=" * 70)
    print("   JDIH MULTI-PORTAL SCRAPER")
    print("=" * 70)

    all_chunks = []
    total_added = 0

    #  Source 1: peraturan.bpk.go.id (with full metadata) 
    print("\n[1] Fetching from peraturan.bpk.go.id...")
    bpk_docs = scrape_bpk(max_docs=80)
    print(f"    Total metadata: {len(bpk_docs)}")

    print("    Fetching details for each document...")
    for i, doc in enumerate(bpk_docs[:30], 1):  # Get details for first 30
        print(f"    [{i}/30] {doc['title'][:50]}...", end=" ", flush=True)
        detail = fetch_bpk_detail(doc["id"])
        if detail:
            doc["abstract"] = detail.get("abstract", "")
            doc["pdf_url"] = detail.get("pdf_url", "")
            doc["full_text"] = detail.get("full_text", "")
        print("OK")
        time.sleep(0.3)

    # Generate content
    for doc in bpk_docs:
        content = doc.get("full_text") or doc.get("abstract") or generate_structured_content(doc)
        chunk = {
            "text": content,
            "metadata": {
                "title": doc["title"],
                "source": "BPK",
                "category": "keuangan",
                "jenis": doc.get("jenis", ""),
                "tahun": doc.get("tahun", ""),
                "subjek": doc.get("subjek", ""),
                "detail_url": doc.get("detail_url", ""),
                "scraped_date": datetime.now().isoformat(),
            }
        }
        all_chunks.append(chunk)
        total_added += 1

    print(f"    [OK] {len(bpk_docs)} documents queued from BPK")

    #  Source 2: jdih.atrbpn.go.id 
    print("\n[2] Fetching from jdih.atrbpn.go.id...")
    atr_docs = scrape_atrbpn(max_docs=50)
    print(f"    Total metadata: {len(atr_docs)}")

    print("    Fetching details for each document...")
    for i, doc in enumerate(atr_docs[:25], 1):
        print(f"    [{i}/25] {doc['title'][:50]}...", end=" ", flush=True)
        detail = fetch_atr_detail(doc["id"])
        if detail:
            doc["description"] = detail.get("description", "")
            doc["json_ld"] = detail.get("json_ld", {})
            doc["pdf_url"] = detail.get("pdf_url", "")
            doc["full_text"] = detail.get("full_text", "")
        print("OK")
        time.sleep(0.3)

    for doc in atr_docs:
        content = doc.get("full_text") or doc.get("description") or generate_structured_content(doc)
        chunk = {
            "text": content,
            "metadata": {
                "title": doc["title"],
                "source": "ATR/BPN",
                "category": "pertanahan",
                "jenis": doc.get("jenis", ""),
                "tahun": doc.get("tahun", ""),
                "subjek": doc.get("subjek", ""),
                "detail_url": doc.get("detail_url", ""),
                "scraped_date": datetime.now().isoformat(),
            }
        }
        all_chunks.append(chunk)
        total_added += 1

    print(f"    [OK] {len(atr_docs)} documents queued from ATR/BPN")

    #  Source 3: Kemenkeu sitemap (metadata-only) 
    print("\n[3] Loading from Kemenkeu sitemap (metadata-only)...")
    kmz_docs = load_kemenkeu_sitemap_urls(limit=150)
    print(f"    Total metadata: {len(kmz_docs)}")

    for doc in kmz_docs:
        content = generate_structured_content(doc)
        chunk = {
            "text": content,
            "metadata": {
                "title": doc["title"],
                "source": "Kemenkeu",
                "category": "keuangan",
                "jenis": doc.get("jenis", ""),
                "tahun": doc.get("tahun", ""),
                "subjek": doc.get("subjek", ""),
                "detail_url": doc.get("detail_url", ""),
                "scraped_date": datetime.now().isoformat(),
            }
        }
        all_chunks.append(chunk)
        total_added += 1

    print(f"    [OK] {len(kmz_docs)} documents queued from Kemenkeu")

    #  Save to JSON 
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = DATA_DIR / f"multi_source_docs_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "fetch_date": datetime.now().isoformat(),
            "total_chunks": len(all_chunks),
            "sources": {
                "BPK": len(bpk_docs),
                "ATR/BPN": len(atr_docs),
                "Kemenkeu": len(kmz_docs)
            },
            "documents": all_chunks
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(all_chunks)} chunks to:")
    print(f"      {output_file}")

    #  Add to vector store 
    print("\n[4] Adding to vector store...")
    try:
        from src.retrieval.simple_vector_store import SimpleVectorStore
        vector_store = SimpleVectorStore()

        for i, chunk in enumerate(all_chunks):
            vector_store.add_documents([chunk])
            if (i + 1) % 20 == 0:
                print(f"    Added {i+1}/{len(all_chunks)}...")

        count = vector_store.count()
        print(f"    [OK] Vector store now has {count} documents")
    except Exception as e:
        print(f"    [WARN] Could not add to vector store: {e}")
        print(f"    [INFO] Data saved to JSON file for manual import")

    print("\n" + "=" * 70)
    print("   SCRAPING COMPLETE!")
    print("=" * 70)
    print(f"Total chunks: {len(all_chunks)}")
    print(f"  - BPK:        {len(bpk_docs)}")
    print(f"  - ATR/BPN:    {len(atr_docs)}")
    print(f"  - Kemenkeu:   {len(kmz_docs)}")
    print(f"Output: {output_file}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()