#!/usr/bin/env python
"""Fetch additional government data from JDIH Atom/RSS feeds"""

import json
import sys
import re
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore
from src.data.chunker import DocumentChunker


def fetch_atom_feed(url, source_name, timeout=15):
    """Fetch and parse Atom/RSS feed"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            entries = re.findall(r'<entry>(.*?)</entry>', response.text, re.DOTALL)
            docs = []
            for entry in entries[:50]:
                title = re.search(r'<title>(.*?)</title>', entry)
                link = re.search(r'<link[^>]*href="(.*?)"', entry)
                date = re.search(r'<published>(.*?)</published>', entry)
                summary = re.search(r'<summary>(.*?)</summary>', entry)

                if title:
                    docs.append({
                        'title': (title.group(1) or '').strip(),
                        'url': link.group(1) if link else '',
                        'date': (date.group(1)[:10] if date else '') or '',
                        'description': (summary.group(1)[:300] if summary else '').strip()
                    })
            return docs
        else:
            print(f"   HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"   Error: {e}")
        return []


def create_content(doc, source):
    """Create searchable content from document metadata"""
    return f"""{doc['title']}

SUMBER: {source}
TANGGAL: {doc['date']}
LINK: {doc['url']}

RINGKASAN:
{doc['description']}

Dokumen ini merupakan produk hukum resmi dari {source} Republik Indonesia.

INSTANSI: {source}
STATUS: Berlaku
""".strip()


def main():
    print("=" * 60)
    print("FETCHING ADDITIONAL GOVERNMENT DATA FROM LIVE SOURCES")
    print("=" * 60)

    chunker = DocumentChunker(chunk_size=300, overlap=30)
    all_chunks = []

    # Sources to fetch
    sources = [
        ('https://peraturan.bpk.go.id/atom.xml', 'JDIH BPK', 'keuangan'),
        ('https://jdih.kemnaker.go.id/atom.xml', 'JDIH Kemnaker', 'ketenagakerjaan'),
        ('https://jdih.setkab.go.id/feed', 'JDIH Setkab', 'pemerintahan'),
    ]

    for url, source_name, category in sources:
        print(f"\nFetching {source_name}...")
        docs = fetch_atom_feed(url, source_name)
        print(f"   Found {len(docs)} documents")

        for doc in docs:
            content = create_content(doc, source_name)

            metadata = {
                'title': doc['title'][:100],
                'category': category,
                'doc_type': f'Peraturan {source_name}',
                'source': source_name,
                'url': doc['url'],
                'date': doc['date'],
                'description': doc['description'],
                'type': 'live_atom_feed'
            }

            chunks = chunker.chunk(
                text=content,
                doc_id=f'{source_name.lower().replace(" ", "_")}_{len(all_chunks)}',
                metadata=metadata
            )

            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    'id': f"{source_name.lower().replace(' ', '_')}_{len(all_chunks)}_{i}",
                    'text': chunk.text,
                    'metadata': metadata
                })

    print(f"\nTotal new chunks prepared: {len(all_chunks)}")

    if all_chunks:
        store = VectorStore()
        initial = store.collection.count()

        print("Adding to vector store...")
        added = store.add_chunks(all_chunks)

        final = store.collection.count()
        print(f"\n[DONE] Added {added} new chunks")
        print(f"Total chunks: {initial} -> {final}")

        # Save report
        report = {
            'date': datetime.now().isoformat(),
            'sources': [s[1] for s in sources],
            'total_added': added,
            'final_count': final
        }

        with open('data/documents/multi_source_load_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Report saved to data/documents/multi_source_load_report.json")
    else:
        print("No new data to add")

    # Show stats
    store = VectorStore()
    stats = store.get_stats()
    print(f"\nFinal vector store stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Categories: {stats['categories']}")


if __name__ == '__main__':
    main()