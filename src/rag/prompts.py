"""
Indonesian-Optimized RAG Prompts

Prompt templates designed for Indonesian government documents.
"""

# System prompt for Indonesian government Q&A
SYSTEM_PROMPT = """Anda adalah asisten AI yang ahli dalam peraturan dan kebijakan pemerintah Indonesia.

Tugas Anda:
1. Menjawab pertanyaan berdasarkan dokumen pemerintah Indonesia yang diberikan
2. Memberikan jawaban yang akurat, jelas, dan mudah dipahami
3. Mengutip pasal atau bagian dokumen yang relevan
4. Jika informasi tidak ada dalam dokumen, nyatakan dengan jelas

Aturan Penting:
- Jawab dalam Bahasa Indonesia yang baik dan benar
- Gunakan format yang terstruktur untuk jawaban yang panjang
- Sertakan referensi dokumen (nama peraturan, pasal, ayat)
- Jangan mengarang informasi yang tidak ada dalam dokumen
- Jika tidak yakin, katakan "Saya tidak menemukan informasi yang cukup"
"""

# User query template
QUERY_TEMPLATE = """Konteks dari Dokumen Pemerintah:
{context}

Pertanyaan: {question}

Berikan jawaban yang:
1. Akurat berdasarkan dokumen di atas
2. Jelas dan mudah dipahami
3. Menyertakan referensi (nama dokumen, pasal jika ada)

Jawaban:"""

# Query template with metadata
QUERY_WITH_METADATA_TEMPLATE = """Dokumen Sumber:
{sources}

Konteks Relevan:
{context}

Pertanyaan Pengguna: {question}

Instruksi:
- Jawab berdasarkan konteks di atas
- Sebutkan dokumen sumber yang digunakan
- Jika ada pasal/ayat, sebutkan nomor spesifiknya
- Jika informasi tidak lengkap, jelaskan keterbatasannya

Jawaban Anda:"""

# Follow-up conversation template
FOLLOWUP_TEMPLATE = """Riwayat Percakapan:
{history}

Dokumen Referensi:
{context}

Pertanyaan Lanjutan: {question}

Jawab pertanyaan lanjutan ini dengan mempertimbangkan riwayat percakapan sebelumnya.

Jawaban:"""


def format_context(chunks: list) -> str:
    """Format retrieved chunks as context."""
    context_parts = []
    
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get('metadata', {}).get('doc_id', 'Unknown')
        text = chunk.get('text', '')
        
        context_parts.append(f"[Dokumen {i}: {source}]\n{text}")
    
    return "\n\n".join(context_parts)


def format_sources(chunks: list) -> str:
    """Format source documents list."""
    sources = []
    seen = set()
    
    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        doc_id = metadata.get('doc_id', 'Unknown')
        
        if doc_id not in seen:
            doc_type = metadata.get('doc_type', '')
            year = metadata.get('year', '')
            
            source_str = f"- {doc_type} {doc_id}"
            if year:
                source_str += f" ({year})"
            
            sources.append(source_str)
            seen.add(doc_id)
    
    return "\n".join(sources) if sources else "Tidak ada sumber"


def build_prompt(
    question: str,
    chunks: list,
    include_metadata: bool = True
) -> str:
    """
    Build complete prompt for RAG query.
    
    Args:
        question: User question
        chunks: Retrieved chunks
        include_metadata: Include source metadata
    
    Returns:
        Formatted prompt string
    """
    context = format_context(chunks)
    
    if include_metadata:
        sources = format_sources(chunks)
        prompt = QUERY_WITH_METADATA_TEMPLATE.format(
            sources=sources,
            context=context,
            question=question
        )
    else:
        prompt = QUERY_TEMPLATE.format(
            context=context,
            question=question
        )
    
    return prompt
