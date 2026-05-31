"""
Load Downloaded PDFs to Vector Store
Processes PDFs from data/documents/pdfs/ and adds to vector database
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import PyPDF2
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.retrieval.vector_search import VectorStore, prepare_chunks_for_indexing
from src.data.chunker import Chunk


def extract_text_from_pdf(pdf_path: str, max_pages: int = 15) -> str:
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total = len(reader.pages)
            pages = min(max_pages, total)

            text = ""
            for i in range(pages):
                page = reader.pages[i]
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"

            return text.strip()
    except Exception as e:
        print(f"    Error reading {pdf_path}: {e}")
        return ""


def generate_doc_id(title: str) -> str:
    """Generate consistent doc_id from title."""
    clean = title.upper().replace(' ', '_')[:40]
    hash_suffix = hashlib.md5(title.encode()).hexdigest()[:6]
    return f"jdih_{clean}_{hash_suffix}"


def load_pdfs_to_vector_store(pdf_dir: str = "data/documents/pdfs", max_docs: int = 50):
    """Load downloaded PDFs into vector store."""

    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        print(f"[ERR] PDF directory not found: {pdf_dir}")
        return 0

    # Get all PDFs
    pdf_files = list(pdf_path.glob("*.pdf"))
    pdf_files = [f for f in pdf_files if f.stat().st_size > 10000]  # Skip tiny files
    pdf_files = pdf_files[:max_docs]

    print(f"[LOAD] Found {len(pdf_files)} PDFs to process")
    print("=" * 60)

    # Initialize vector store
    store = VectorStore()
    initial_count = store.collection.count() if hasattr(store, 'collection') else 0
    print(f"[INFO] Current vector store: {initial_count} docs\n")

    all_chunks = []
    chunk_id = initial_count

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.stem[:50]}")

        # Extract text
        text = extract_text_from_pdf(str(pdf_file))

        if not text or len(text) < 500:
            print(f"    [WARN] Skipping - text too short or empty")
            continue

        # Generate metadata
        filename = pdf_file.stem
        parts = filename.split('_')

        doc_type = parts[1] if len(parts) > 1 else "Lainnya"
        year = parts[2] if len(parts) > 2 else "2026"
        title = ' '.join(parts[3:]) if len(parts) > 3 else filename

        doc_id = generate_doc_id(filename)

        # Create chunk
        chunk = {
            'id': doc_id,
            'text': text[:8000],  # Limit text length
            'metadata': {
                'source': 'JDIH Kemenkeu',
                'title': filename.replace('_', ' '),
                'doc_type': doc_type,
                'year': year,
                'file_path': str(pdf_file),
                'file_size': pdf_file.stat().st_size,
                'category': 'keuangan',
                'text_length': len(text),
                'downloaded_at': datetime.now().isoformat()
            }
        }

        all_chunks.append(chunk)
        print(f"    [OK] Extracted {len(text)} chars -> chunk ready")

    if not all_chunks:
        print("\n[ERR] No valid chunks to add")
        return 0

    print(f"\n[LOAD] Adding {len(all_chunks)} chunks to vector store...")

    # Prepare chunks for indexing
    prepared = prepare_chunks_for_indexing([
        Chunk(
            doc_id=c['id'],
            chunk_id=i,
            text=c['text'],
            start_char=0,
            end_char=len(c['text']),
            num_tokens=len(c['text'].split()),
            metadata=c['metadata']
        )
        for i, c in enumerate(all_chunks)
    ])

    # Add to vector store
    store.add_chunks(prepared, show_progress=True)

    final_count = store.collection.count()
    added = final_count - initial_count

    print("\n" + "=" * 60)
    print(f"[OK] SUCCESS!")
    print(f"    PDFs processed: {len(pdf_files)}")
    print(f"    Chunks added:  {added}")
    print(f"    Total in DB:   {final_count}")
    print("=" * 60)

    return added


def save_metadata_report(pdf_dir: str = "data/documents/pdfs"):
    """Save metadata report of downloaded PDFs."""
    pdf_path = Path(pdf_dir)
    pdf_files = list(pdf_path.glob("*.pdf"))

    metadata = {
        'generated_at': datetime.now().isoformat(),
        'total_pdfs': len(pdf_files),
        'source': 'JDIH Kemenkeu',
        'documents': []
    }

    for pdf_file in pdf_files:
        if pdf_file.stat().st_size < 10000:
            continue

        text = extract_text_from_pdf(str(pdf_file))
        filename = pdf_file.stem
        parts = filename.split('_')

        metadata['documents'].append({
            'filename': pdf_file.name,
            'doc_type': parts[1] if len(parts) > 1 else 'Lainnya',
            'year': parts[2] if len(parts) > 2 else '2026',
            'size_kb': pdf_file.stat().st_size // 1024,
            'text_chars': len(text),
            'preview': text[:200] if text else 'N/A'
        })

    # Save report
    report_path = Path("data/documents/pdf_metadata_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[REPORT] Saved to: {report_path}")
    return metadata


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   PDF LOADER - JDIH DOCUMENTS")
    print("=" * 60 + "\n")

    # Step 1: Load PDFs to vector store
    added = load_pdfs_to_vector_store(max_docs=30)

    # Step 2: Save metadata report
    print("\n[GENERATING] Metadata report...")
    metadata = save_metadata_report()

    print(f"\n[DONE] Total PDFs processed: {metadata['total_pdfs']}")
    print("       Vector store updated with government document chunks!")