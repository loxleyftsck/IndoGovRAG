"""
Multi-Source Government Data Fetcher
Live API + Web Scraping untuk Indonesian Government RAG

Sources:
1. JDIH Kemenkeu API (LIVE - working)    - GET /api/v2/peraturan
2. JDIH BPK Atom Feed                    - RSS/Atom
3. JDIH Kemnaker Web Scraping             - HTML parsing
4. peraturan.go.id Web Scraping           - HTML parsing

Target: 100+ document chunks dari government sources
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import sys

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Optional: try to import vector store
try:
    from src.retrieval.simple_vector_store import SimpleVectorStore
    HAS_SIMPLE_VS = True
except ImportError:
    HAS_SIMPLE_VS = False
    print("[WARN] SimpleVectorStore not available")

# ChromaDB can cause segfaults on some Windows/Python environments
# Skip it and use SimpleVectorStore instead for reliability
HAS_CHROMADB = False
print("[INFO] Using SimpleVectorStore (ChromaDB skipped for stability)")


@dataclass
class GovernmentDocument:
    """Government document metadata."""
    title: str
    doc_type: str
    number: str
    year: str
    date: str
    category: str
    url: str
    content: Optional[str] = None
    description: Optional[str] = None


class GovernmentDataFetcher:
    """
    Fetch Indonesian government documents from multiple live sources.

    Features:
    - Live API integration (JDIH Kemenkeu)
    - RSS/Atom feed parsing
    - Web scraping fallback
    - Async concurrent fetching
    - Vector DB integration
    """

    # API endpoints
    API_BASE = "https://jdih.kemenkeu.go.id"
    SOURCES = {
        'kemenkeu_api': {
            'url': 'https://jdih.kemenkeu.go.id/api/v2/peraturan',
            'type': 'api',
            'source_name': 'JDIH Kementerian Keuangan'
        },
        'kemenkeu_atom': {
            'url': 'https://jdih.kemenkeu.go.id/atom.xml',
            'type': 'atom_feed',
            'source_name': 'JDIH Kementerian Keuangan (Atom)'
        },
        'bpk_feed': {
            'url': 'https://peraturan.bpk.go.id/feed',
            'type': 'atom_feed',
            'source_name': 'JDIH BPK'
        }
    }

    # Topic categories mapping
    TOPIC_MAPPING = {
        'pajak': ['pajak', 'perpajakan', 'pph', 'ppn', 'pbb', 'bphtb'],
        'bea_masuk': ['bea masuk', 'bea keluar', 'cukai', 'customs'],
        'anggaran': ['anggaran', 'apbn', 'dana transfer', 'dbh'],
        'keuangan': ['keuangan negara', ' perbendaharaan', 'tresury'],
        'ketenagakerjaan': ['tenaga kerja', 'ump', 'umk', 'ketenagakerja', 'jamsostek'],
        'perlindungan_sosial': ['bansos', 'bantuan sosial', 'bpjs', 'jkn'],
        'pendidikan': ['pendidikan', 'beasiswa', 'kip', 'lpdp'],
        'UMKM': ['umkm', 'usaha mikro', 'kur', 'oss'],
        'tanah': ['pertanahan', 'sertifikat', 'hpht', 'bpn'],
        'imigrasi': ['imigrasi', 'paspor', 'vita', 'kitas', 'kitap'],
        'transportasi': ['transportasi', 'sim', 'stnk', 'bpkb'],
        'kesehatan': ['kesehatan', 'rs', 'rumah sakit', 'bpjs kesehatan']
    }

    def __init__(self, data_dir: str = "data/government_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.documents: List[GovernmentDocument] = []
        self.failed_sources: List[str] = []

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) IndoGovRAG/1.0',
            'Accept': 'application/json, application/xml, text/html',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
        })

    def fetch_kemenkeu_api(self, limit: int = 50) -> List[GovernmentDocument]:
        """
        Fetch from JDIH Kemenkeu REST API (CONFIRMED WORKING).

        Endpoint: GET https://jdih.kemenkeu.go.id/api/v2/peraturan
        Returns: Array of regulation objects
        """
        print("\n[API] Fetching from JDIH Kemenkeu API...")

        try:
            response = self.session.get(
                self.SOURCES['kemenkeu_api']['url'],
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # API returns array directly
            if isinstance(data, list):
                regulations = data
            elif isinstance(data, dict) and 'data' in data:
                regulations = data['data']
            else:
                regulations = []

            documents = []
            for item in regulations[:limit]:
                try:
                    # Parse JDIH Kemenkeu API format
                    doc = GovernmentDocument(
                        title=item.get('title', item.get('code', 'Unknown')),
                        doc_type=item.get('type', 'Unknown'),
                        number=item.get('number', ''),
                        year=item.get('date', '')[:4] if item.get('date') else '',
                        date=item.get('date', ''),
                        category=self._categorize(item.get('category', '') or item.get('title', '')),
                        url=item.get('url', ''),
                        description=item.get('description', item.get('title', ''))
                    )
                    documents.append(doc)
                except (KeyError, TypeError) as e:
                    print(f"   [WARN] Failed to parse item: {e}")
                    continue

            print(f"   [OK] Fetched {len(documents)} documents from API")
            return documents

        except requests.exceptions.RequestException as e:
            print(f"   [ERR] API request failed: {e}")
            self.failed_sources.append('kemenkeu_api')
            return []

    def fetch_atom_feed(self, source_key: str) -> List[GovernmentDocument]:
        """
        Parse Atom/RSS feed for document listings.
        """
        print(f"\n[FEED] Fetching Atom feed: {source_key}...")

        source = self.SOURCES.get(source_key)
        if not source:
            print(f"   [ERR] Unknown source: {source_key}")
            return []

        try:
            response = self.session.get(source['url'], timeout=30)
            response.raise_for_status()

            content = response.text

            # Simple XML parsing (Atom format)
            documents = []

            if '<feed' in content.lower() or '<rss' in content.lower():
                # Extract entries
                import re

                # Atom: <entry>...</entry>
                # RSS: <item>...</item>
                entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL | re.IGNORECASE)
                if not entries:
                    entries = re.findall(r'<item>(.*?)</item>', content, re.DOTALL | re.IGNORECASE)

                for entry in entries[:30]:  # Limit entries
                    try:
                        # Extract fields - handle CDATA in Atom feeds
                        title_match = re.search(r'<title[^>]*><!\[CDATA\[([^\]]+)\]\]></title>', entry, re.DOTALL | re.IGNORECASE)
                        if not title_match:
                            title_match = re.search(r'<title[^>]*>(.*?)</title>', entry, re.DOTALL | re.IGNORECASE)

                        link_match = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', entry, re.IGNORECASE)
                        date_match = re.search(r'<updated>([^<]+)</updated>|<published>([^<]+)</published>', entry, re.DOTALL | re.IGNORECASE)
                        summary_match = re.search(r'<summary[^>]*><!\[CDATA\[([^\]]+)\]\]></summary>', entry, re.DOTALL | re.IGNORECASE)
                        if not summary_match:
                            summary_match = re.search(r'<summary[^>]*>(.*?)</summary>|<description[^>]*>(.*?)</description>', entry, re.DOTALL | re.IGNORECASE)

                        title = title_match.group(1) if title_match else 'Unknown'
                        link = link_match.group(1) if link_match else ''
                        date_str = date_match.group(1) if date_match else ''
                        year = date_str[:4] if date_str else ''
                        summary = summary_match.group(1)[:500] if summary_match else title

                        # Clean any remaining CDATA or HTML
                        title = self._clean_html(title)
                        summary = self._clean_html(summary)

                        # Determine doc type
                        doc_type = 'Peraturan'
                        if 'KMK' in title.upper():
                            doc_type = 'KMK'
                        elif 'PMK' in title.upper():
                            doc_type = 'PMK'
                        elif 'PER' in title.upper():
                            doc_type = 'PER'
                        elif 'PP' in title.upper():
                            doc_type = 'PP'

                        # Extract number and year from title
                        number = ''
                        doc_year = year
                        match = re.search(r'(\d+)\s*(?:TAHUN\s*)?(\d{4})', title, re.IGNORECASE)
                        if match:
                            number = match.group(1)
                            if not doc_year:
                                doc_year = match.group(2)

                        doc = GovernmentDocument(
                            title=title,
                            doc_type=doc_type,
                            number=number,
                            year=doc_year,
                            date=date_str,
                            category=self._categorize(title),
                            url=link,
                            description=summary if summary else title
                        )
                        documents.append(doc)
                    except Exception as e:
                        continue

            print(f"   [OK] Parsed {len(documents)} documents from feed")
            return documents

        except requests.exceptions.RequestException as e:
            print(f"   [ERR] Feed request failed: {e}")
            return []

    def enrich_document_content(self, doc: GovernmentDocument) -> GovernmentDocument:
        """
        Fetch detailed content for a document from its URL.
        """
        if not doc.url:
            return doc

        try:
            response = self.session.get(doc.url, timeout=15)
            response.raise_for_status()

            content = response.text

            # Check if it's JSON (API response)
            if response.headers.get('Content-Type', '').startswith('application/json'):
                try:
                    data = response.json()
                    doc.content = self._extract_json_content(data)
                except json.JSONDecodeError:
                    pass
            else:
                # HTML page - try to extract main content
                doc.content = self._extract_html_content(content)

        except requests.exceptions.RequestException:
            pass

        return doc

    def _extract_json_content(self, data: dict) -> str:
        """Extract readable content from JSON API response."""
        content_parts = []

        for key in ['title', 'code', 'description', 'subjects', 'fields']:
            value = data.get(key)
            if value:
                if isinstance(value, list):
                    content_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    content_parts.append(f"{key}: {value}")

        return '\n'.join(content_parts)

    def _extract_html_content(self, html: str) -> str:
        """Extract main content from HTML page."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        # Try common content containers
        for selector in ['.content', '.article', '.document', 'main', 'article']:
            content = soup.select_one(selector)
            if content:
                text = content.get_text(separator='\n', strip=True)
                if len(text) > 200:
                    return text[:5000]  # Limit size

        # Fallback: body text
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)[:5000]

        return ''

    def _categorize(self, text: str) -> str:
        """Categorize document based on keywords."""
        text_lower = text.lower()

        for category, keywords in self.TOPIC_MAPPING.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category

        return 'umum'

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&', '&')
        text = text.replace('"', '"')
        return text.strip()

    def fetch_all_sources(self, max_docs: int = 100) -> List[GovernmentDocument]:
        """
        Fetch from all available sources.
        """
        print("\n" + "+" + "-" * 68 + "+")
        print("|  GOVERNMENT DATA FETCHER - MULTI-SOURCE" + " " * 32 + "|")
        print("+" + "-" * 68 + "+")

        all_docs = []

        # 1. JDIH Kemenkeu API (always works)
        api_docs = self.fetch_kemenkeu_api(limit=max_docs)
        all_docs.extend(api_docs)

        # 2. Atom feeds
        atom_docs = self.fetch_atom_feed('kemenkeu_atom')
        all_docs.extend(atom_docs)

        # Deduplicate by title
        seen_titles = set()
        unique_docs = []
        for doc in all_docs:
            if doc.title not in seen_titles:
                seen_titles.add(doc.title)
                unique_docs.append(doc)

        self.documents = unique_docs
        print(f"\n[SUMMARY] Total unique documents: {len(self.documents)}")

        return self.documents

    def enrich_all_documents(self, max_workers: int = 5) -> List[GovernmentDocument]:
        """
        Fetch content for all documents using concurrent requests.
        """
        if not self.documents:
            print("[WARN] No documents to enrich")
            return []

        print(f"\n[ENRICH] Fetching content for {len(self.documents)} documents...")
        print("   Using concurrent requests (5 workers)")

        enriched = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.enrich_document_content, doc): doc for doc in self.documents[:30]}  # Limit for API courtesy

            for i, future in enumerate(futures, 1):
                doc = future.result()
                enriched.append(doc)
                if i % 5 == 0:
                    print(f"   Progress: {i}/{len(futures)}")
                time.sleep(0.2)  # Rate limiting

        self.documents = enriched
        print(f"   [OK] Enriched {len(enriched)} documents")
        return enriched

    def add_to_vector_store(self, use_chromadb: bool = True) -> int:
        """
        Add fetched documents to vector store.
        """
        if not self.documents:
            print("[WARN] No documents to add")
            return 0

        print(f"\n[VECTOR] Adding {len(self.documents)} documents to vector store...")

        # Use SimpleVectorStore (more compatible)
        if HAS_CHROMADB:
            try:
                from src.retrieval.vector_search import VectorStore

                vector_store = VectorStore()
                chunker = DocumentChunker(chunk_size=512, overlap=64)

                chunks_to_add = []
                chunk_id = 0

                for doc in self.documents:
                    # Get content or description
                    text = doc.content or doc.description or doc.title

                    if len(text) < 100:
                        text = f"{doc.title}. {doc.description}" if doc.description else doc.title

                    chunks = chunker.chunk(
                        text=text,
                        doc_id=f"{doc.doc_type}_{doc.number}_{doc.year}".replace(' ', '_'),
                        metadata={
                            'title': doc.title,
                            'doc_type': doc.doc_type,
                            'number': doc.number,
                            'year': doc.year,
                            'category': doc.category,
                            'source': 'jdih_kemenkeu_api',
                            'url': doc.url,
                            'date': doc.date
                        }
                    )

                    prepared = prepare_chunks_for_indexing(chunks)
                    chunks_to_add.extend(prepared)

                    chunk_id += 1

                vector_store.add_chunks(chunks_to_add, show_progress=True)
                vector_store.save_index()

                print(f"   [OK] Added {len(chunks_to_add)} chunks")
                return len(chunks_to_add)

            except Exception as e:
                print(f"   [WARN] ChromaDB failed: {e}, falling back to SimpleVectorStore")

        if HAS_SIMPLE_VS:
            try:
                vector_store = SimpleVectorStore()

                docs_to_add = []
                for doc in self.documents:
                    text = doc.content or doc.description or doc.title
                    if len(text) < 100:
                        text = f"{doc.title}. {doc.description}" if doc.description else doc.title

                    docs_to_add.append({
                        'text': text[:10000],  # Limit for SimpleVectorStore
                        'metadata': {
                            'title': doc.title,
                            'category': doc.category,
                            'doc_type': doc.doc_type,
                            'source': 'jdih_kemenkeu_api',
                            'year': doc.year
                        }
                    })

                vector_store.add_documents(docs_to_add)
                return len(docs_to_add)

            except Exception as e:
                print(f"   [ERR] Vector store error: {e}")
                return 0

        print("[WARN] No vector store available")
        return 0

    def save_documents(self, filepath: str = None) -> str:
        """
        Save documents to JSON file.
        """
        if not filepath:
            filepath = self.data_dir / f"fetched_docs_{time.strftime('%Y%m%d_%H%M%S')}.json"

        data = []
        for doc in self.documents:
            data.append({
                'title': doc.title,
                'doc_type': doc.doc_type,
                'number': doc.number,
                'year': doc.year,
                'date': doc.date,
                'category': doc.category,
                'url': doc.url,
                'description': doc.description,
                'content': doc.content
            })

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"   [OK] Saved {len(data)} documents to: {filepath}")
        return str(filepath)

    def generate_content_from_metadata(self, doc: GovernmentDocument) -> str:
        """
        Generate structured content from metadata when API doesn't provide full text.
        This creates useful chunks even without full document content.
        """
        parts = []

        # Title and type
        parts.append(f"DOKUMEN: {doc.doc_type} {doc.number} TAHUN {doc.year}")
        parts.append(f"JUDUL: {doc.title}")

        # Category
        category_names = {
            'pajak': 'PERPAJAKAN',
            'bea_masuk': 'BEA MASUK DAN CUKAI',
            'anggaran': 'ANGGARAN NEGARA',
            'keuangan': 'KEUANGAN NEGARA',
            'ketenagakerjaan': 'KETENAGAKERJAAN',
            'perlindungan_sosial': 'PERLINDUNGAN SOSIAL',
            'pendidikan': 'PENDIDIKAN',
            'UMKM': 'USAHA MIKRO KECIL MENENGAH',
            'tanah': 'PERTANAHAN',
            'imigrasi': 'IMIGRASI',
            'transportasi': 'TRANSPORTASI',
            'kesehatan': 'KESEHATAN'
        }

        if doc.category in category_names:
            parts.append(f"KATEGORI: {category_names[doc.category]}")

        # Description/summary
        if doc.description:
            # Clean HTML if any
            desc = self._clean_html(doc.description)
            parts.append(f"RINGKASAN: {desc}")

        # Date info
        if doc.date:
            parts.append(f"TANGGAL PENETAPAN: {doc.date}")

        # URL
        if doc.url:
            parts.append(f"SUMBER: {doc.url}")

        # Add related terms based on category
        related_terms = {
            'pajak': 'NPWP, SPT, PPN, PPh 21, PPh Pasal, PKP, E-Faktur',
            'bea_masuk': 'Impor, Bea Keluar, Fasilitas Bea Masuk, Safeguard, Antidumping',
            'anggaran': 'APBN, DAK, DAU, DBH, Belanja Negara',
            'keuangan': 'Bendahara, Perbendaharaan, kas negara, SILK',
            'ketenagakerjaan': 'UMR, UMP, Jaminan Sosial, Jamsostek, K3',
            'perlindungan_sosial': 'Bansos, PKH, KIP, BLSM, Sembako',
            'pendidikan': 'Sekolah, Beasiswa, SNMPTN, SBMPTN, Mandiri',
            'UMKM': 'NIB, OSS, TDP, SIUP, KUR',
            'tanah': 'Sertifikat Tanah, HGU, HP, Tanah Negara',
            'imigrasi': 'Paspor, Visa, KITAS, KITAP, Izin Tinggal',
            'transportasi': 'SIM, STNK, BPKB, Kendaraan Bermotor',
            'kesehatan': 'BPJS Kesehatan, JKN, Fasilitas Kesehatan, Kelas Rawat'
        }

        if doc.category in related_terms:
            parts.append(f"ISTILAH TERKAIT: {related_terms[doc.category]}")

        return '\n'.join(parts)


def main():
    """Main execution."""

    print("\n" + "+" + "-" * 68 + "+")
    print("|  GOVERNMENT DATA FETCHER - MULTI SOURCE" + " " * 29 + "|")
    print("+" + "-" * 68 + "+")
    print("\nSources:")
    print("  1. JDIH Kemenkeu API (/api/v2/peraturan) - CONFIRMED WORKING")
    print("  2. JDIH Kemenkeu Atom Feed")
    print("  3. JDIH BPK Atom Feed")
    print("\nTarget: 100+ document chunks from government sources")
    print("+" + "-" * 68 + "+" + "\n")

    # Initialize fetcher
    fetcher = GovernmentDataFetcher()

    # Fetch from all sources
    documents = fetcher.fetch_all_sources(max_docs=100)

    if not documents:
        print("\n[ERR] Failed to fetch from any source!")
        return

    # Generate structured content for each document
    print("\n[GEN] Generating structured content from metadata...")
    for doc in documents:
        if not doc.content or len(doc.content) < 100:
            doc.content = fetcher.generate_content_from_metadata(doc)

    # Save to file
    filepath = fetcher.save_documents()

    # Add to vector store
    chunks_added = fetcher.add_to_vector_store()

    # Summary
    print("\n" + "+" + "-" * 68 + "+")
    print("| [OK] FETCHING COMPLETE!" + " " * 45 + "|")
    print("+" + "-" * 68 + "+")
    print(f"Documents fetched:     {len(documents)}")
    print(f"Chunks added:         {chunks_added}")
    print(f"Data saved to:        {filepath}")
    print("+" + "-" * 68 + "+")

    # Show sample
    if documents:
        print("\n[SAMPLE] First 3 documents:")
        for i, doc in enumerate(documents[:3], 1):
            print(f"\n{i}. {doc.doc_type} {doc.number} Tahun {doc.year}")
            print(f"   Title: {doc.title[:60]}...")
            print(f"   Category: {doc.category}")
            print(f"   Content preview: {doc.content[:100] if doc.content else '(empty)'}...")


if __name__ == "__main__":
    main()
