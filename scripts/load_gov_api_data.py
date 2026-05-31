"""
Load Government API Data to Vector Store

Loads fetched JDIH Kemenkeu data (from feed.json API) into vector store.
Uses the official /api/v2/peraturan endpoint that was confirmed working.
"""

import json
import glob
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore, prepare_chunks_for_indexing
from src.data.chunker import Chunk, DocumentChunker


def find_best_data_file():
    """Find the best data file to load."""
    files = glob.glob('data/government_data/*.json')

    # Filter to relevant files
    relevant = []
    for f in files:
        basename = Path(f).name
        if 'jdih_kemenkeu' in basename or 'multi_source' in basename:
            with open(f, 'r', encoding='utf-8') as fh:
                try:
                    data = json.load(fh)
                    if isinstance(data, list) and len(data) > 0:
                        relevant.append((f, len(data)))
                except Exception:
                    pass

    if not relevant:
        return None

    # Return largest
    return max(relevant, key=lambda x: x[1])[0]


def load_gov_api_data():
    """Load government API data into vector store."""

    print("[CONFIG] Loading Government API Data...")
    print()

    # Find data file
    data_file = find_best_data_file()

    if not data_file:
        print("[ERR] No data file found in data/government_data/")
        return 0

    print(f"[LOAD] Data file: {data_file}")

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Handle dict format (multi_source)
        docs = data.get('documents', [])
    else:
        # Handle list format (jdih_kemenkeu_feed)
        docs = data

    print(f"[STAT] Found {len(docs)} documents")
    print()

    # Initialize vector store
    print("Vector Store...")
    store = VectorStore()
    initial_count = store.collection.count()
    print(f"   Initial count: {initial_count}")

    # Initialize chunker
    chunker = DocumentChunker(chunk_size=512, overlap=64, min_chunk_size=50)

    # Process documents
    chunks_to_add = []
    chunk_id_start = initial_count

    for i, doc in enumerate(docs):
        # Get text content
        if isinstance(doc, dict):
            text = doc.get('content', doc.get('text', ''))
            title = doc.get('title', 'N/A')
            doc_id = doc.get('doc_id', f'gov_api_{i+1:03d}')
            doc_type = doc.get('doc_type', 'Unknown')
            category = doc.get('category', 'umum')
            source = doc.get('source', 'JDIH Kemenkeu API')
            url = doc.get('url', '')
            date = doc.get('date', '')
        else:
            text = str(doc)
            title = 'N/A'
            doc_id = f'gov_api_{i+1:03d}'
            doc_type = 'Unknown'
            category = 'umum'
            source = 'JDIH Kemenkeu API'
            url = ''
            date = ''

        # Skip if no content
        if not text or len(text) < 50:
            # Generate content from metadata
            text = generate_content(doc, title, doc_type, category, url, date)

        # Create metadata
        metadata = {
            'title': title,
            'doc_type': doc_type,
            'category': category,
            'source': source,
            'url': url,
            'date': date,
            'source_file': data_file,
            'loaded_at': datetime.now().isoformat()
        }

        # Chunk document
        doc_chunks = chunker.chunk(text, doc_id, metadata)

        # Update chunk IDs
        for chunk in doc_chunks:
            chunk.chunk_id = chunk_id_start
            chunk_id_start += 1

        chunks_to_add.extend(doc_chunks)

        if i < 3:
            print(f" Doc {i+1}: {title[:50]}...")
            print(f"      Chunks: {len(doc_chunks)}, Type: {doc_type}, Category: {category}")

    print()
    print(f"[STAT] Total chunks to add: {len(chunks_to_add)}")

    if not chunks_to_add:
        print("[WARN] No chunks to add")
        return 0

    # Prepare for indexing
    print("[PREP] Preparing chunks for indexing...")
    prepared = prepare_chunks_for_indexing(chunks_to_add)

    # Add to vector store
    print("[ADD] Adding to vector store...")
    store.add_chunks(prepared, show_progress=True)

    # Verify
    final_count = store.collection.count()
    added = final_count - initial_count

    print()
    print("=" * 60)
    print(f"[OK] Successfully loaded!")
    print(f"      Initial: {initial_count}")
    print(f"      Added:      {added}")
    print(f"      Final:      {final_count}")
    print("=" * 60)

    # Test search
    print()
    print("[TEST] Testing search...")
    test_queries = [
        "PMK perpajakan",
        "KMK bea masuk",
        "peraturan menteri keuangan"
    ]

    for query in test_queries:
        results = store.search(query, n_results=2)
        if results:
            print(f"   Query: '{query}'")
            print(f"   Results: {len(results)}")
            for r in results[:1]:
                print(f"      - Score: {r.score:.3f}, Title: {r.metadata.get('title', 'N/A')[:40]}")

    print()
    print(f"Vector store ready with {final_count} chunks!")

    return added


def generate_content(doc, title, doc_type, category, url, date):
    """Generate structured content from metadata."""

    lines = [
        f"PERATURAN: {title}",
        f"JENIS: {doc_type}",
        f"KATEGORI: {category}",
        f"SUMBER: JDIH Kementerian Keuangan",
        f"URL: {url}",
        f"TANGGAL: {date}",
        "",
        "DESKRIPSI:",
    ]

    # Add description based on type
    if doc_type == 'PMK':
        lines.append(f"Peraturan Menteri Keuangan (PMK) dengan judul '{title}' adalah regulasi")
        lines.append("yang diterbitkan oleh Kementerian Keuangan Republik Indonesia.")
        lines.append("PMK mengatur berbagai aspek perpajakan, bea cukai, dan keuangan negara.")
    elif doc_type == 'KMK':
        lines.append(f"Keputusan Menteri Keuangan (KMK) dengan judul '{title}' adalah regulasi")
        lines.append("yang diterbitkan oleh Kementerian Keuangan Republik Indonesia.")
        lines.append("KMK biasanya mengatur teknis pelaksanaan dari PMK atau undang-undang.")
    elif doc_type == 'PER':
        lines.append(f"Peraturan Direktorat Jenderal (PER) dengan judul '{title}' adalah regulasi")
        lines.append("yang diterbitkan oleh Direktorat Jenderal di bawah Kementerian Keuangan.")
    elif doc_type == 'PP':
        lines.append(f"Peraturan Pemerintah (PP) dengan judul '{title}' adalah regulasi")
        lines.append("yang diterbitkan oleh Pemerintah Republik Indonesia.")
    else:
        lines.append(f"Dokumen regulasi dengan judul '{title}'.")
        lines.append("Merupakan peraturan resmi dari Kementerian Keuangan Indonesia.")

    # Add related terms by category
    related_terms = {
        'keuangan': 'perpajakan, PPN, PPh, Bea Masuk, Bea Keluar, Cukai, PNBP, Kurs, THR',
        'perpajakan': 'NPWP, SPT, PPh, PPN, BPHTB, PKP, E-Faktur, Pasal 21, Pasal 22',
        'bea_cukai': 'Bea Masuk, Bea Keluar, Cukai, Importir, Eksportir, HS Code',
        'penerimaan_negara': 'PNBP, Penerimaan Negara, Pajak, Retribusi',
 }

    if category in related_terms:
        lines.append("")
        lines.append(f"TOPIK TERKAIT: {related_terms[category]}")

    return '\n'.join(lines)


if __name__ == "__main__":
    load_gov_api_data()
