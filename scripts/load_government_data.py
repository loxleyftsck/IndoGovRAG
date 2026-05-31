"""
Load Government Data to Vector Store
Consolidates data from all sources and loads to vector database
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.retrieval.vector_search import VectorStore
from src.data.chunker import Chunk


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    """Generate unique chunk ID."""
    return f"{doc_id}_chunk_{chunk_index}"


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 150) -> list:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def consolidate_all_data():
    """Consolidate data from all JSON files."""
    data_dir = Path('data/government_data')
    consolidated = []

    # Pattern untuk file government data
    patterns = ['*.json']

    files = sorted(data_dir.glob('*.json'), key=lambda x: x.stat().st_mtime)

    print(f"[SCAN] Found {len(files)} JSON files in government_data/")
    print()

    seen_ids = set()

    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)

            docs = []
            if isinstance(data, list):
                docs = data
            elif isinstance(data, dict):
                docs = data.get('documents', data.get('generated_content', []))

            for doc in docs:
                doc_id = doc.get('doc_id', '')
                title = doc.get('title', doc.get('name', ''))

                if not title:
                    continue

                # Create unique ID based on title + date
                unique_key = f"{title}_{doc.get('date', '')}_{doc.get('year', '')}"

                if unique_key in seen_ids:
                    continue
                seen_ids.add(unique_key)

                # Process content
                content = doc.get('content', '')
                description = doc.get('description', '')

                # Use content or generate from metadata
                if content and len(content) > 50:
                    text = content
                elif description:
                    text = f"{title}\n\n{description}"
                else:
                    text = f"{title}\n\n{doc.get('summary', '')}"

                if len(text) < 50:
                    continue

                consolidated.append({
                    'title': title,
                    'text': text,
                    'doc_type': doc.get('doc_type', doc.get('type', 'Unknown')),
                    'category': doc.get('category', 'general'),
                    'year': doc.get('year', doc.get('tahun', '')),
                    'date': doc.get('date', ''),
                    'source': doc.get('source', 'JDIH Kemenkeu'),
                    'url': doc.get('url', ''),
                    'metadata': doc.get('metadata', {})
                })

        except Exception as e:
            print(f"  [WARN] Error reading {f.name}: {e}")
            continue

    print(f"[CONSOLIDATE] Total unique documents: {len(consolidated)}")
    return consolidated


def load_to_vector_store(documents: list, max_chunks: int = 500):
    """Load documents to vector store."""

    if not documents:
        print("[ERR] No documents to load!")
        return 0

    store = VectorStore()
    initial_count = store.collection.count() if hasattr(store, 'collection') else 0
    print(f"[INFO] Current vector store: {initial_count} docs\n")

    all_chunks = []

    # Process each document
    for i, doc in enumerate(documents):
        title = doc.get('title', 'Unknown')
        text = doc.get('text', '')
        category = doc.get('category', 'general')

        if not text or len(text) < 100:
            continue

        # Generate doc_id
        doc_id = hashlib.md5(title.encode()).hexdigest()[:12]
        doc_id = f"gov_{category}_{doc_id}"

        # Split into chunks
        text_parts = chunk_text(text, chunk_size=1500, overlap=150)

        for j, part in enumerate(text_parts):
            chunk_id = generate_chunk_id(doc_id, j)

            chunk = {
                'id': chunk_id,
                'text': part,
                'metadata': {
                    'title': title,
                    'category': category,
                    'doc_type': doc.get('doc_type', 'Unknown'),
                    'year': doc.get('year', ''),
                    'source': doc.get('source', 'JDIH'),
                    'url': doc.get('url', ''),
                    'doc_id': doc_id,
                    'chunk_index': j,
                    'created_at': datetime.now().isoformat()
                }
            }

            all_chunks.append(chunk)

    print(f"[PROCESS] Created {len(all_chunks)} chunks from {len(documents)} documents")

    # Limit chunks
    if len(all_chunks) > max_chunks:
        all_chunks = all_chunks[:max_chunks]
        print(f"[LIMIT] Truncated to {max_chunks} chunks")

    # Prepare for indexing
    prepared = []
    for c in all_chunks:
        chunk_obj = Chunk(
            doc_id=c['metadata']['doc_id'],
            chunk_id=c['metadata']['chunk_index'],
            text=c['text'],
            start_char=0,
            end_char=len(c['text']),
            num_tokens=len(c['text'].split()),
            metadata=c['metadata']
        )

        prepared.append({
            'id': c['id'],
            'text': c['text'],
            'metadata': {
                **c['metadata'],
                'doc_id': chunk_obj.doc_id,
                'chunk_id': chunk_obj.chunk_id,
                'num_tokens': chunk_obj.num_tokens,
            }
        })

    # Add to vector store
    if prepared:
        print(f"[LOAD] Adding {len(prepared)} chunks to vector store...")
        store.add_chunks(prepared, show_progress=True)

    final_count = store.collection.count()
    added = final_count - initial_count

    print("\n" + "=" * 60)
    print(f"[OK] SUCCESS!")
    print(f"    Documents processed: {len(documents)}")
    print(f"    Chunks created:      {len(all_chunks)}")
    print(f"    Chunks added:        {added}")
    print(f"    Total in DB:         {final_count}")
    print("=" * 60)

    # Save index info
    store.save_index()

    return added


def main():
    """Main execution."""
    print()
    print("=" * 60)
    print("   GOVERNMENT DATA LOADER")
    print("   Consolidating + Loading to Vector Store")
    print("=" * 60)
    print()

    # Consolidate all data
    documents = consolidate_all_data()

    if not documents:
        print("\n[ERR] No documents found!")
        return

    # Load to vector store
    added = load_to_vector_store(documents)

    print(f"\n[DONE] Loaded {added} new chunks to vector store!")


if __name__ == "__main__":
    main()