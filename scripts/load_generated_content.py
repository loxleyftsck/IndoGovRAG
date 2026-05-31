"""
Load Generated Government Content to Vector Store
Processes structured content and adds to vector database
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


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 100) -> list:
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


def load_content_to_vector_store(data_path: str = "data/fetched_raw_data.json", max_chunks: int = 200):
    """Load generated content into vector store."""

    # Read raw data
    data_file = Path(data_path)
    if not data_file.exists():
        print(f"[ERR] Data file not found: {data_path}")
        print("      Run fetch_additional_sources.py first!")
        return 0

    with open(data_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    generated = raw_data.get('generated_content', [])
    print(f"[LOAD] Found {len(generated)} topics in raw data")

    # Initialize vector store
    store = VectorStore()
    initial_count = store.collection.count() if hasattr(store, 'collection') else 0
    print(f"[INFO] Current vector store: {initial_count} docs\n")

    all_chunks = []
    chunk_counter = initial_count

    # Process each topic
    for topic in generated:
        title = topic.get('title', 'Unknown')
        text = topic.get('text', '')
        category = topic.get('category', 'general')

        if not text or len(text) < 100:
            continue

        # Generate doc_id
        doc_id = hashlib.md5(title.encode()).hexdigest()[:12]
        doc_id = f"gen_{category}_{doc_id}"

        # Split into chunks
        text_parts = chunk_text(text, chunk_size=1500, overlap=150)

        for i, part in enumerate(text_parts):
            chunk_id = generate_chunk_id(doc_id, i)

            chunk = {
                'id': chunk_id,
                'text': part,
                'metadata': {
                    'title': title,
                    'category': category,
                    'source': 'Generated Content',
                    'doc_id': doc_id,
                    'chunk_index': i,
                    'created_at': datetime.now().isoformat()
                }
            }

            all_chunks.append(chunk)

    print(f"[PROCESS] Created {len(all_chunks)} chunks from {len(generated)} topics")

    # Limit chunks
    if len(all_chunks) > max_chunks:
        all_chunks = all_chunks[:max_chunks]
        print(f"[LIMIT] Truncated to {max_chunks} chunks")

    # Prepare for indexing
    prepared = []
    for i, c in enumerate(all_chunks):
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
        store.add_chunks(prepared, show_progress=True)

    final_count = store.collection.count()
    added = final_count - initial_count

    print("\n" + "=" * 60)
    print(f"[OK] SUCCESS!")
    print(f"    Topics processed: {len(generated)}")
    print(f"    Chunks created:  {len(all_chunks)}")
    print(f"    Chunks added:    {added}")
    print(f"    Total in DB:     {final_count}")
    print("=" * 60)

    # Save index info
    store.save_index()

    return added


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   CONTENT LOADER - GENERATED GOVERNMENT DATA")
    print("=" * 60 + "\n")

    added = load_content_to_vector_store()
    print(f"\n[DONE] Vector store updated with {added} new chunks!")