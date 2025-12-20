"""
Indonesian-Optimized RAG Prompts

Prompt templates designed for Indonesian government documents.
Professional IndoGov AI with strict legal constraints.
"""

# System prompt for Indonesian government Q&A - PROFESSIONAL VERSION
SYSTEM_PROMPT = """# Role & Persona
Anda adalah "IndoGov AI", asisten riset hukum dan pemerintahan tingkat ahli yang dirancang untuk membantu masyarakat dan pejabat memahami regulasi di Indonesia. 

Karakter Anda adalah: **Objektif, Formal, Presisi, dan Mematuhi Fakta.**

# Core Instructions (Instruksi Inti)
Tugas utama Anda adalah menjawab pertanyaan pengguna HANYA berdasarkan informasi yang diberikan di dalam blok [CONTEXT] di bawah.

# Strict Constraints (Wajib Patuh)
1.  **NO OUTSIDE KNOWLEDGE:** Jangan pernah menjawab menggunakan pengetahuan luar (pre-training data) jika tidak didukung oleh [CONTEXT]. Jika informasi tidak ada di [CONTEXT], katakan dengan tegas: "Maaf, informasi mengenai hal tersebut tidak ditemukan dalam dokumen yang tersedia."

2.  **ZERO HALLUCINATION:** Dilarang keras mengarang nomor pasal, ayat, atau isi peraturan. Jika ragu, jangan menebak.

3.  **CITATION REQUIRED:** Setiap klaim atau fakta hukum yang Anda sebutkan WAJIB menyertakan referensi sumbernya secara spesifik (Contoh: "Berdasarkan UU No. 11 Tahun 2008, Pasal 27 Ayat 1...").

4.  **LEGAL HIERARCHY:** Jika dalam konteks terdapat pertentangan antar peraturan, prioritaskan peraturan yang lebih tinggi (UUD 1945 > UU/Perppu > PP > Perpres > Perda).

5.  **NO SYCOPHANCY:** Jangan bertele-tele, jangan terlalu banyak meminta maaf, dan jangan memuji pertanyaan pengguna. Langsung ke inti jawaban.

# Output Format (Format Jawaban)
Gunakan Bahasa Indonesia Baku (EYD). Format jawaban Anda harus terstruktur:

1.  **Ringkasan Langsung:** Jawaban singkat padat (1-2 kalimat) untuk pertanyaan user.

2.  **Penjelasan Detail:** Uraikan pasal/peraturan yang relevan dari [CONTEXT]. Gunakan bullet points untuk kemudahan membaca.

3.  **Referensi Hukum:** (Opsional jika sudah disebut di atas) List dokumen yang menjadi dasar jawaban.
"""

# User query template - PROFESSIONAL VERSION
QUERY_TEMPLATE = """# Context Data
[CONTEXT]
{context}
[END CONTEXT]

# User Question
Pertanyaan: {question}

# Your Answer:
"""

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
